SET search_path TO cafae, public;
INSERT INTO usuarios(usuario,nombre_completo,password_hash,rol_id)
 SELECT 'admin_prueba','Administrador sintético','HASH_FICTICIO_SIN_ACCESO',id FROM roles WHERE codigo='ADMINISTRADOR';
INSERT INTO programas(codigo,nombre,orden) VALUES ('P','Programa de prueba',1);
INSERT INTO programas(codigo,nombre,orden,padre_id) VALUES ('P1','Nivel de prueba',2,1);
INSERT INTO partidas_presupuestarias(codigo,descripcion) VALUES ('21.11.21','Partida de prueba');
INSERT INTO metas(codigo,descripcion,programa_id,partida_id) VALUES ('11','Meta de prueba',2,1);
INSERT INTO niveles(nombre) VALUES ('Inicial de prueba');
INSERT INTO nivel_metas(nivel_id,meta_id) VALUES (1,1);
INSERT INTO instituciones(codigo_modular,nombre,nivel_id,distrito,meta_id)
 VALUES ('0000001','Institución sintética',1,'Distrito de prueba',1);
INSERT INTO areas_sede(nombre,meta_id) VALUES ('Área sintética',1);
INSERT INTO categorias(codigo,descripcion) VALUES ('AE','Categoría de prueba');
INSERT INTO trabajadores(dni,apellidos,nombres,tipo,institucion_id,nivel_id,categoria_id,importe,cuenta_multired)
 VALUES ('00000001','Apellido prueba','Persona uno','IIEE',1,1,1,1350,'0001234567');
INSERT INTO trabajadores(dni,apellidos,nombres,tipo,institucion_id,nivel_id,categoria_id,importe,activo)
 VALUES ('00000002','Apellido prueba','Persona inactiva','IIEE',1,1,1,1350,false);
INSERT INTO trabajadores(dni,apellidos,nombres,tipo,area_id,categoria_id,importe,cuenta_multired)
 VALUES ('00000003','Apellido prueba','Persona sede','SEDE',1,1,1500,'0007654321');
INSERT INTO firmas(nombre_completo,cargo) VALUES
 ('Firma sintética uno','Dirección'),('Firma sintética dos','Gestión Institucional'),
 ('Firma sintética tres','Gestión Administrativa'),('Firma sintética cuatro','Finanzas');
INSERT INTO periodos(anio,mes) VALUES (2026,9),(2026,10);
INSERT INTO planillas(periodo_id,tipo,creada_por) VALUES (1,'IIEE',1),(1,'SEDE',1),(2,'IIEE',1);
INSERT INTO planilla_versiones(planilla_id,numero,origen,version_calculo,creada_por)
 VALUES (1,1,'MAESTRO','decimal-half-up-v1',1),(2,1,'MAESTRO','decimal-half-up-v1',1);
INSERT INTO planilla_versiones(planilla_id,numero,origen,fuente_version_id,version_calculo,creada_por)
 VALUES (3,1,'COPIA',1,'decimal-half-up-v1',1);
INSERT INTO planilla_programas(version_id,programa_id,codigo,nombre,orden) VALUES (1,1,'P','Programa histórico',1);
INSERT INTO planilla_programas(version_id,programa_id,padre_id,codigo,nombre,orden) VALUES (1,2,1,'P1','Nivel histórico',2);
INSERT INTO planilla_detalle(version_id,trabajador_id,orden,dni,apellidos,nombres,institucion_id,
 institucion_nombre,meta_id,meta_codigo,meta_descripcion,categoria,cuenta_multired,importe,neto,programa_snapshot_id,partida_codigo)
 VALUES (1,1,1,'00000001','Apellido histórico','Persona uno',1,'Institución histórica',1,'11','Meta histórica',
 'AE','0001234567',1350,0,2,'21.11.21'),
 (3,1,1,'00000001','Apellido histórico','Persona uno',1,'Institución histórica',1,'11','Meta histórica',
 'AE','0001234567',1350,0,NULL,'21.11.21');
INSERT INTO planilla_detalle(version_id,trabajador_id,orden,dni,apellidos,nombres,area_id,area_nombre,
 meta_id,meta_codigo,categoria,cuenta_multired,importe,neto)
 VALUES (2,3,1,'00000003','Apellido histórico','Persona sede',1,'Área histórica',1,'11','AE','0007654321',1500,0);
INSERT INTO planilla_firmas(version_id,posicion,firma_id,nombre_completo,cargo)
 SELECT 1,id,id,nombre_completo,cargo FROM firmas;
INSERT INTO planilla_firmas(version_id,posicion,firma_id,nombre_completo,cargo)
 SELECT 2,CASE id WHEN 4 THEN 3 ELSE id END,id,nombre_completo,cargo FROM firmas WHERE id IN (1,2,4);
INSERT INTO archivos(nombre_original,clave_almacenamiento,mime_type,bytes,sha256,creado_por)
 VALUES ('prueba.txt','pruebas/original','text/plain',1,repeat('a',64),1);
