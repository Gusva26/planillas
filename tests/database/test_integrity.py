"""Pruebas reales de PostgreSQL. Solo datos sintéticos en una base nueva y descartable."""
import concurrent.futures
import json
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from migrate import CONTAINER, database_name, migrate, psql

DB='cafae_test_'+uuid.uuid4().hex[:12]

def assert_sql(condition):
    return f"DO $$ BEGIN IF ({condition}) IS DISTINCT FROM true THEN RAISE EXCEPTION 'Aserción SQL fallida'; END IF; END $$;"

def expect(sql, state='23514'):
    return f"""DO $case$ DECLARE fallido boolean:=false; BEGIN
      BEGIN EXECUTE $cmd${sql}$cmd$; EXCEPTION WHEN SQLSTATE '{state}' THEN fallido:=true; END;
      IF NOT fallido THEN RAISE EXCEPTION 'Se esperaba SQLSTATE {state}'; END IF; END $case$;"""

def close(version):
    return f"""UPDATE cafae.planilla_versiones v SET estado='CERRADA',cerrada_por=1,cerrada_en=now(),
      total_trabajadores=(SELECT count(*) FROM cafae.planilla_detalle WHERE version_id=v.id),
      total_importe=(SELECT sum(importe) FROM cafae.planilla_detalle WHERE version_id=v.id),
      total_descuentos=(SELECT sum(total_descuentos) FROM cafae.planilla_detalle WHERE version_id=v.id),
      total_neto=(SELECT sum(neto) FROM cafae.planilla_detalle WHERE version_id=v.id) WHERE v.id={version};"""

class Integrity(unittest.TestCase):
    def run_sql(self, body, role='cafae_admin'):
        psql(f"BEGIN; SET search_path TO cafae,public; SET LOCAL cafae.usuario_id='1'; SET LOCAL ROLE {role};\n"+body+'\nROLLBACK;',DB)

    def test_calculo_obligatorio(self):
        self.run_sql("INSERT INTO planilla_descuentos(detalle_id,tipo_descuento_id,monto,actualizado_por) VALUES(1,1,735.45,1),(1,6,10,1);"+
            assert_sql("(SELECT total_descuentos=745.45 AND neto=604.55 FROM planilla_detalle WHERE id=1)"))

    def test_licencia_extremos_y_redondeo(self):
        self.run_sql("UPDATE planilla_detalle SET dias_licencia=3 WHERE id=1;"+
            assert_sql("(SELECT monto_licencia=135 AND neto=1215 FROM planilla_detalle WHERE id=1)")+
            "UPDATE planilla_detalle SET dias_licencia=30 WHERE id=1;"+
            assert_sql("(SELECT monto_licencia=1350 AND neto=0 FROM planilla_detalle WHERE id=1)")+
            "UPDATE planilla_detalle SET importe=1370,dias_licencia=1 WHERE id=1;"+
            assert_sql("(SELECT monto_licencia=45.67 AND neto=1324.33 FROM planilla_detalle WHERE id=1)")+
            expect("UPDATE planilla_detalle SET dias_licencia=31 WHERE id=1")+
            expect("UPDATE planilla_detalle SET dias_licencia=-1 WHERE id=1"))

    def test_dinero_invalido(self):
        for value in ['-1',"'NaN'", "'Infinity'"]:
            with self.subTest(value=value):
                self.run_sql(expect(f"UPDATE planilla_detalle SET importe={value} WHERE id=1",'22003' if value=="'Infinity'" else '23514'))

    def test_ocho_descuentos_sin_duplicar_licencia(self):
        self.run_sql("INSERT INTO planilla_descuentos(detalle_id,tipo_descuento_id,monto,actualizado_por) SELECT 1,id,id,1 FROM tipos_descuento;"+
          "UPDATE planilla_detalle SET dias_licencia=1 WHERE id=1;"+
          assert_sql("(SELECT total_descuentos=73 AND monto_licencia=45 AND neto=1277 FROM planilla_detalle WHERE id=1)")+
          "DELETE FROM planilla_descuentos WHERE detalle_id=1;"+
          assert_sql("(SELECT total_descuentos=45 FROM planilla_detalle WHERE id=1)"))

    def test_no_acepta_totales_manuales(self):
        self.run_sql("UPDATE planilla_detalle SET total_descuentos=999,neto=1,monto_licencia=400 WHERE id=1;"+
          assert_sql("(SELECT total_descuentos=0 AND neto=1350 AND monto_licencia=0 FROM planilla_detalle WHERE id=1)"))

    def test_periodo_tipo_y_dni_unicos(self):
        self.run_sql(expect("INSERT INTO periodos(anio,mes) VALUES(2026,9)",'23505')+
          expect("INSERT INTO planillas(periodo_id,tipo,creada_por) VALUES(1,'IIEE',1)",'23505')+
          expect("INSERT INTO trabajadores(dni,apellidos,nombres,tipo) VALUES('00000001','x','x','IIEE')",'23505')+
          assert_sql("(SELECT count(*)=2 FROM planillas WHERE periodo_id=1)"))

    def test_firmas_segun_tipo(self):
        self.run_sql(expect("INSERT INTO planilla_firmas(version_id,posicion,firma_id,nombre_completo,cargo) VALUES(2,4,3,'Prueba','Cargo')")+
          "DELETE FROM planilla_firmas WHERE version_id=1 AND posicion=4;"+expect(close(1))+close(2)+
          assert_sql("(SELECT estado='CERRADA' FROM planilla_versiones WHERE id=2)"))

    def test_cierre_datos_incompletos(self):
        for field in ('meta_codigo','categoria','cuenta_multired','institucion_nombre'):
            with self.subTest(field=field):
                self.run_sql(f'UPDATE planilla_detalle SET {field}=NULL WHERE id=1;'+expect(close(1)))

    def test_negativo_permitido_en_borrador_no_cierre(self):
        self.run_sql("INSERT INTO planilla_descuentos(detalle_id,tipo_descuento_id,monto,actualizado_por) VALUES(1,1,1400,1);"+
          assert_sql("(SELECT neto=-50 FROM planilla_detalle WHERE id=1)")+expect(close(1)))

    def test_totales_de_cierre_deben_conciliar(self):
        self.run_sql(expect("UPDATE planilla_versiones SET estado='CERRADA',cerrada_por=1,cerrada_en=now(),total_trabajadores=1,total_importe=10,total_descuentos=0,total_neto=10 WHERE id=1"))

    def test_snapshot_no_cambia_con_maestros(self):
        self.run_sql(close(1)+"UPDATE trabajadores SET importe=1800,apellidos='Nuevo' WHERE id=1; UPDATE firmas SET nombre_completo='Firma cambiada' WHERE id=1; UPDATE metas SET codigo='99' WHERE id=1; UPDATE programas SET nombre='Programa nuevo' WHERE id=1;"+
          assert_sql("(SELECT importe=1350 AND apellidos='Apellido histórico' AND meta_codigo='11' FROM planilla_detalle WHERE id=1)")+
          assert_sql("(SELECT nombre_completo='Firma sintética uno' FROM planilla_firmas WHERE version_id=1 AND posicion=1)")+
          assert_sql("(SELECT nombre='Programa histórico' FROM planilla_programas WHERE id=1)"))

    def test_cierre_inmutable_incluso_sql_directo(self):
        cmds=["UPDATE planilla_versiones SET estado='BORRADOR' WHERE id=1",
          "DELETE FROM planilla_versiones WHERE id=1",
          "UPDATE planilla_detalle SET importe=2000 WHERE id=1",
          "DELETE FROM planilla_detalle WHERE id=1",
          "UPDATE planilla_detalle SET version_id=3 WHERE id=1",
          "INSERT INTO planilla_descuentos(detalle_id,tipo_descuento_id,monto,actualizado_por) VALUES(1,1,10,1)",
          "UPDATE planilla_firmas SET cargo='Otro' WHERE version_id=1",
          "DELETE FROM planilla_firmas WHERE version_id=1",
          "UPDATE planilla_programas SET nombre='Otro' WHERE version_id=1",
          "INSERT INTO observaciones_planilla(version_id,revision_validada,codigo,severidad,descripcion) VALUES(1,1,'X','ERROR','Prueba')"]
        # Dueño de migración también está sujeto a triggers (no a superuser desactivándolos).
        self.run_sql(close(1)+''.join(expect(s) for s in cmds),role='cafae_migrator')

    def test_descuentos_cerrados_no_actualizables_ni_eliminables(self):
        self.run_sql("INSERT INTO planilla_descuentos(detalle_id,tipo_descuento_id,monto,actualizado_por) VALUES(1,1,10,1);"+close(1)+
          expect("UPDATE planilla_descuentos SET monto=20 WHERE detalle_id=1")+
          expect("DELETE FROM planilla_descuentos WHERE detalle_id=1"))

    def test_reapertura_versiona_y_no_duplica_reportes(self):
        self.run_sql(close(1)+"INSERT INTO planilla_versiones(planilla_id,numero,origen,fuente_version_id,motivo_reapertura,version_calculo,creada_por) VALUES(1,2,'REAPERTURA',1,'Corrección de prueba','decimal-half-up-v1',1);"+
          assert_sql("(SELECT count(*)=1 FROM ultimos_cierres WHERE planilla_id=1)")+
          assert_sql("(SELECT importe=1350 FROM remuneraciones_por_meta WHERE version_id=1)")+
          assert_sql("EXISTS(SELECT 1 FROM auditoria WHERE accion='REABRIR_PLANILLA')")+
          expect("INSERT INTO planilla_versiones(planilla_id,numero,origen,fuente_version_id,motivo_reapertura,version_calculo,creada_por) VALUES(1,3,'REAPERTURA',1,'Otra','v1',1)"))

    def test_copia_requiere_mes_anterior_mismo_tipo(self):
        self.run_sql("INSERT INTO periodos(anio,mes) VALUES(2027,1); INSERT INTO planillas(periodo_id,tipo,creada_por) SELECT id,'IIEE',1 FROM periodos WHERE anio=2027 AND mes=1;"+
          expect("INSERT INTO planilla_versiones(planilla_id,numero,origen,fuente_version_id,version_calculo,creada_por) SELECT id,1,'COPIA',1,'v1',1 FROM planillas WHERE periodo_id=(SELECT id FROM periodos WHERE anio=2027 AND mes=1)"))

    def test_control_revision_obsoleta(self):
        self.run_sql("DO $$ DECLARE previa bigint; BEGIN SELECT revision_edicion INTO previa FROM planilla_versiones WHERE id=1; PERFORM bloquear_edicion(1,previa); BEGIN PERFORM bloquear_edicion(1,previa); RAISE EXCEPTION 'No rechazó revisión vieja'; EXCEPTION WHEN serialization_failure THEN NULL; END; END $$;")

    def test_operacion_cierre_controla_revision_y_actor(self):
        self.run_sql(expect('SELECT cerrar_planilla(1,NULL,1)','40001')+
          expect('SELECT cerrar_planilla(1,0,1)','40001')+
          expect('SELECT cerrar_planilla(1,1,999)','42501')+
          'SELECT cerrar_planilla(1,(SELECT revision_edicion FROM planilla_versiones WHERE id=1),1);'+
          assert_sql("(SELECT estado='CERRADA' AND total_importe=1350 FROM planilla_versiones WHERE id=1)"))

    def test_programas_sin_ciclos(self):
        self.run_sql(expect('UPDATE programas SET padre_id=2 WHERE id=1'))

    def test_programas_historicos_sin_ciclos(self):
        self.run_sql(expect('UPDATE planilla_programas SET padre_id=2 WHERE id=1'))

    def test_roles_consulta_sin_escritura_ni_secretos(self):
        self.run_sql(expect('UPDATE trabajadores SET importe=1 WHERE id=1','42501')+
          expect('SELECT password_hash FROM usuarios','42501')+
          expect('SELECT token_hash FROM sesiones','42501')+
          expect('SELECT * FROM archivos','42501'),role='cafae_consulta')

    def test_operador_no_cierra_ni_administra(self):
        self.run_sql(expect(close(1),'42501')+
          expect("UPDATE firmas SET nombre_completo='Intruso' WHERE id=1",'42501')+
          expect('ALTER TABLE planilla_detalle DISABLE TRIGGER ALL','42501')+
          expect('TRUNCATE planilla_detalle CASCADE','42501'),role='cafae_operador')

    def test_auditoria_append_only_sin_hash(self):
        self.run_sql("UPDATE usuarios SET password_hash='OTRO_HASH_DE_PRUEBA' WHERE id=1; UPDATE trabajadores SET importe=1400 WHERE id=1;"+
          assert_sql("EXISTS(SELECT 1 FROM auditoria a JOIN auditoria_cambios c ON c.auditoria_id=a.id WHERE a.usuario_id=1 AND c.campo='importe' AND c.valor_nuevo='1400.00')")+
          assert_sql("NOT EXISTS(SELECT 1 FROM auditoria_cambios WHERE campo IN ('password_hash','token_hash'))")+
          expect("UPDATE auditoria SET descripcion='cambio'",'42501')+expect('DELETE FROM auditoria','42501'))

    def test_auditoria_protegida_para_propietario(self):
        self.run_sql(expect("UPDATE auditoria SET descripcion='cambio'")+expect('TRUNCATE auditoria CASCADE'),role='cafae_migrator')

    def test_importacion_match_y_duplicados(self):
        self.run_sql("""INSERT INTO importaciones(version_id,tipo_descuento_id,archivo_id,revision_previsualizada,idempotencia,version_extractor,creada_por)
          VALUES(1,1,1,1,gen_random_uuid(),'prueba',1);
          INSERT INTO importacion_detalle(importacion_id,version_id,fila,dni_normalizado,monto_validado,detalle_planilla_id,estado,seleccionado)
          SELECT max(id),1,1,'00000001',10,1,'IDENTIFICADO',true FROM importaciones;"""+
          expect("INSERT INTO importacion_detalle(importacion_id,version_id,fila,dni_normalizado,monto_validado,detalle_planilla_id,estado,seleccionado) SELECT max(id),1,2,'00000001',20,1,'IDENTIFICADO',true FROM importaciones",'23505')+
          expect("INSERT INTO importacion_detalle(importacion_id,version_id,fila,dni_normalizado,monto_validado,detalle_planilla_id,estado,seleccionado) SELECT max(id),1,3,'99999999',10,1,'IDENTIFICADO',true FROM importaciones")+
          expect("INSERT INTO importacion_detalle(importacion_id,version_id,fila,detalle_planilla_id,estado) SELECT max(id),1,4,2,'REVISAR' FROM importaciones",'23503'))

    def test_importacion_aplicada_inmutable(self):
        self.run_sql("""INSERT INTO importaciones(version_id,tipo_descuento_id,archivo_id,revision_previsualizada,idempotencia,version_extractor,creada_por)
          VALUES(1,1,1,1,gen_random_uuid(),'prueba',1);
          INSERT INTO importacion_detalle(importacion_id,version_id,fila,estado) SELECT max(id),1,1,'REVISAR' FROM importaciones;
          UPDATE importaciones SET estado='APLICADA',modo='ACTUALIZAR',aplicada_por=1,aplicada_en=now(),registros_aplicados=1,total_aplicado=10;
          """+expect("UPDATE importacion_detalle SET monto_original='editado'")+expect("UPDATE importaciones SET total_aplicado=20"))

    def test_documentos_no_generables_en_abierta_y_txt_pendiente(self):
        self.run_sql("INSERT INTO plantillas_documento(tipo,version,archivo_referencia_id,validada_por,validada_en) VALUES('BOLETA','v1',1,1,now()),('TXT_BANCARIO','v1',1,1,now());"+
          expect("INSERT INTO documentos_generados(version_id,detalle_id,plantilla_id,archivo_id,tipo,version_generador,registros,total_referencia,generado_por) SELECT 1,1,id,1,'BOLETA_INDIVIDUAL','v1',1,1350,1 FROM plantillas_documento WHERE tipo='BOLETA'")+
          close(1)+expect("INSERT INTO documentos_generados(version_id,plantilla_id,archivo_id,tipo,version_generador,registros,total_referencia,generado_por) SELECT 1,id,1,'TXT','v1',1,1350,1 FROM plantillas_documento WHERE tipo='TXT_BANCARIO'"))

    def test_fk_y_rollback_de_lote(self):
        self.run_sql("""DO $$ BEGIN
          BEGIN
            UPDATE trabajadores SET importe=999 WHERE id=1;
            INSERT INTO trabajadores(dni,apellidos,nombres,tipo,institucion_id) VALUES('00000009','Prueba','FK','IIEE',999999);
          EXCEPTION WHEN foreign_key_violation THEN NULL; END;
          END $$;"""+assert_sql('(SELECT importe=1350 FROM trabajadores WHERE id=1)'))

def container(*args, input=None):
    return subprocess.run(['docker','exec','-i',CONTAINER,*args],input=input,capture_output=True,check=True)

def wait_sleep(name):
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        if psql(f"SELECT count(*) FROM pg_stat_activity WHERE application_name='{name}' AND wait_event='PgSleep';",DB).stdout.strip()=='1':
            return
        time.sleep(.05)
    raise AssertionError('La primera sesión no alcanzó el punto de sincronización')

def concurrency_checks():
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        revision=int(psql('SELECT revision_edicion FROM cafae.planilla_versiones WHERE id=1;',DB).stdout.strip())
        writer=pool.submit(psql,"SET application_name='cafae_test_writer'; BEGIN; SET ROLE cafae_operador; UPDATE cafae.planilla_detalle SET importe=1450 WHERE id=1; SELECT pg_sleep(1.5); COMMIT;",DB)
        wait_sleep('cafae_test_writer')
        closer=pool.submit(psql,f'SET ROLE cafae_admin; SELECT cafae.cerrar_planilla(1,{revision},1);',DB,False)
        writer.result(); stale=closer.result()
        if stale.returncode==0 or 'cambió' not in stale.stderr:
            raise AssertionError('El cierre no detectó cambios posteriores a la revisión')
        psql('SET ROLE cafae_admin; SELECT cafae.cerrar_planilla(1,(SELECT revision_edicion FROM cafae.planilla_versiones WHERE id=1),1);',DB)
        psql(assert_sql('(SELECT total_importe=1450 AND total_neto=1450 FROM cafae.planilla_versiones WHERE id=1)'),DB)
        # Cierre primero: el escritor espera y después debe rechazar la versión cerrada.
        closer=pool.submit(psql,"SET application_name='cafae_test_closer'; BEGIN; SET ROLE cafae_admin; "+close(2)+" SELECT pg_sleep(1.5); COMMIT;",DB)
        wait_sleep('cafae_test_closer')
        late=pool.submit(psql,"SET ROLE cafae_operador; UPDATE cafae.planilla_detalle SET importe=500 WHERE version_id=2;",DB,False)
        closer.result()
        result=late.result()
        if result.returncode==0 or 'cerrada' not in result.stderr:
            raise AssertionError('Escritura concurrente posterior al cierre no fue rechazada')
        # Guardado optimista: dos operaciones con la misma revisión, una debe abortar.
        revision=int(psql('SELECT revision_edicion FROM cafae.planilla_versiones WHERE id=3;',DB).stdout.strip())
        first=pool.submit(psql,f"SET application_name='cafae_test_revision'; BEGIN; SET ROLE cafae_operador; SELECT cafae.bloquear_edicion(3,{revision}); SELECT pg_sleep(1.5); COMMIT;",DB)
        wait_sleep('cafae_test_revision')
        second=pool.submit(psql,f'SET ROLE cafae_operador; SELECT cafae.bloquear_edicion(3,{revision});',DB,False)
        first.result(); result=second.result()
        if result.returncode==0 or 'cambió' not in result.stderr:
            raise AssertionError('No se detectó guardado con revisión obsoleta')
        # Un snapshot repetible antiguo tampoco puede introducir un ciclo de catálogo.
        psql("SET ROLE cafae_admin; INSERT INTO cafae.programas(codigo,nombre,orden) VALUES('X','Raíz X',3),('Y','Raíz Y',4);",DB)
        older=pool.submit(psql,"SET application_name='cafae_test_tree'; BEGIN ISOLATION LEVEL REPEATABLE READ; SET ROLE cafae_admin; SELECT count(*) FROM cafae.programas; SELECT pg_sleep(1.5); UPDATE cafae.programas SET padre_id=(SELECT id FROM cafae.programas WHERE codigo='X') WHERE codigo='Y'; COMMIT;",DB,False)
        wait_sleep('cafae_test_tree')
        psql("SET ROLE cafae_admin; UPDATE cafae.programas SET padre_id=(SELECT id FROM cafae.programas WHERE codigo='Y') WHERE codigo='X';",DB)
        result=older.result()
        if result.returncode==0 or 'serialize' not in result.stderr:
            raise AssertionError('El árbol permitió una actualización desde un snapshot antiguo')
    print('OK: 4 escenarios de concurrencia con dos sesiones reales')

def restore_check():
    target=database_name(DB+'_restore')
    container('createdb','-U','cafae_migrator',target)
    try:
        dump=container('pg_dump','-U','cafae_migrator','-Fc',DB).stdout
        container('pg_restore','-U','cafae_migrator','--exit-on-error','--no-owner','-d',target,input=dump)
        for table in ('trabajadores','planilla_versiones','planilla_detalle','planilla_firmas','auditoria'):
            query=f"SELECT md5(string_agg(row_to_json(t)::text,'|' ORDER BY id)) FROM cafae.{table} t;"
            if psql(query,DB).stdout != psql(query,target).stdout:
                raise AssertionError('Restauración distinta: '+table)
        print('OK: backup y restauración en base separada con conciliación de contenido')
    finally:
        container('dropdb','-U','cafae_migrator',target)

if __name__=='__main__':
    created=False
    try:
        container('createdb','-U','cafae_migrator',DB); created=True
        migrate(DB); migrate(DB)  # reejecución idempotente
        psql((ROOT/'tests'/'database'/'fixture.sql').read_text(encoding='utf-8'),DB)
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Integrity)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
        concurrency_checks()
        restore_check()
        dest=ROOT/'test-results';dest.mkdir(exist_ok=True)
        (dest/'database.json').write_text(json.dumps({'unit_integration':result.testsRun,
          'concurrency':4,'restore':1,'migration_rerun':1,'ok':True},indent=2),encoding='utf-8')
    finally:
        if created:
            container('dropdb','-U','cafae_migrator',database_name(DB))
