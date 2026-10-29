/**
 * Tipos de dominio compartidos por la UI.
 *
 * Reflejan el contrato del API (`cafae/api/schemas.py` y los servicios de
 * `cafae/*.py`). Si un campo no existe en el backend, no debe estar acá.
 */
import type { Pagina } from './api/types';

export type Rol = 'ADMINISTRADOR' | 'PLANILLAS' | 'CONSULTA';
export type TipoPlanilla = 'IIEE' | 'SEDE';
export type EstadoVersion = 'BORRADOR' | 'REVISION' | 'CERRADA';

export interface User {
  id: number;
  username: string;
  nombre: string;
  rol: Rol;
  debe_cambiar_password: boolean;
}

export interface UserAccount {
  id: number;
  usuario: string;
  nombre_completo: string;
  rol: Rol;
  activo: boolean;
  debe_cambiar_password: boolean;
  revision: number;
}

/** Última versión de una planilla, tal como la devuelve `/api/reportes/dashboard`. */
export interface ResumenPlanillaDashboard {
  id: number;
  anio: number;
  mes: number;
  tipo: TipoPlanilla;
  version_id: number;
  numero: number;
  estado: EstadoVersion;
  total_trabajadores: number;
  total_importe: number;
  total_descuentos: number;
  total_neto: number;
  cerrada_en?: string | null;
}

export interface DashboardSummary {
  iiee: ResumenPlanillaDashboard | null;
  sede: ResumenPlanillaDashboard | null;
  trabajadores_activos: number;
  instituciones_activas: number;
  alertas_neto_negativo: number;
}

export interface Trabajador {
  id: number;
  dni: string;
  apellidos: string;
  nombres: string;
  tipo: TipoPlanilla;
  institucion_id?: number;
  institucion_nombre?: string;
  area_id?: number;
  area_nombre?: string;
  nivel_id?: number;
  nivel_nombre?: string;
  cargo_id?: number;
  cargo_nombre?: string;
  categoria_id?: number;
  categoria_codigo?: string;
  situacion_id?: number;
  situacion_nombre?: string;
  subtipo_id?: number;
  subtipo_nombre?: string;
  fecha_nacimiento?: string;
  ley?: string;
  regimen_laboral?: string;
  jornada_laboral?: string;
  cuenta_multired?: string;
  importe: number;
  activo: boolean;
  tipo_pago?: string;
  numero_cheque?: string;
  tiempo_servicio_texto?: string;
  leyenda_permanente?: string;
  regimen_pensionario?: string;
  fecha_ingreso?: string;
  fecha_termino?: string;
  revision?: number;
}

export interface PlanillaCreada {
  planilla_id: number;
  version_id: number;
  trabajadores_copiados: number;
  /** Revisión vigente tras insertar el detalle (nunca es 1). */
  revision_edicion: number;
}

export interface RespuestaCreacionPlanilla {
  ok: boolean;
  planilla: PlanillaCreada;
  mensaje: string;
}

/** Cuerpo de `POST /api/trabajadores` y `PUT /api/trabajadores/{id}`. */
export interface TrabajadorPayload {
  dni: string;
  apellidos: string;
  nombres: string;
  tipo: TipoPlanilla;
  institucion_id: number | null;
  area_id: number | null;
  nivel_id: number | null;
  cargo_id: number | null;
  situacion_id: number | null;
  categoria_id: number | null;
  fecha_nacimiento: string | null;
  regimen_laboral: string;
  jornada_laboral: string;
  regimen_pensionario: string | null;
  tiempo_servicio_texto: string | null;
  fecha_ingreso: string | null;
  fecha_termino: string | null;
  leyenda_permanente: string | null;
  tipo_pago: string;
  numero_cheque: string | null;
  cuenta_multired: string | null;
  importe: number;
  revision?: number;
}

export interface PlanillaListItem {
  id: number;
  tipo: TipoPlanilla;
  anio: number;
  mes: number;
  version_id: number;
  version_numero: number;
  version_estado: EstadoVersion;
  version_origen: string;
  revision_edicion: number;
  total_trabajadores: number;
  total_importe: number;
  total_descuentos: number;
  total_neto: number;
  cerrada_en?: string;
  cerrada_por_nombre?: string;
  creada_por_nombre: string;
}

/** Valor de una celda de detalle: los conceptos de descuento son dinámicos. */
export type ValorLinea = number | string | Record<string, number> | undefined;

export interface LineaPlanilla {
  id: number;
  version_id: number;
  trabajador_id: number;
  orden: number;
  dni: string;
  apellidos: string;
  nombres: string;
  cargo?: string;
  cargo_nombre?: string;
  categoria_codigo?: string;
  cuenta_multired?: string;
  institucion_nombre?: string;
  area_nombre?: string;
  importe: number;
  dias_licencia: number;
  monto_licencia: number;
  pichincha?: number;
  sullana?: number;
  subcafae?: number;
  brenta?: number;
  sitrase?: number;
  fentase?: number;
  otros?: number;
  total_descuentos: number;
  neto: number;
  descuentos?: Record<string, number>;
  /** Los códigos de descuento llegan del catálogo, no se pueden enumerar aquí. */
  [concepto: string]: ValorLinea;
}

/** Cabecera de una versión de planilla. */
export interface PlanillaVersion {
  id: number;
  planilla_id: number;
  numero: number;
  estado: EstadoVersion;
  origen: string;
  revision_edicion: number;
  tipo: TipoPlanilla;
  anio: number;
  mes: number;
  cantidad_firmas: number;
  total_trabajadores: number;
  total_importe: number;
  total_descuentos: number;
  total_neto: number;
  creada_en?: string;
  creada_por?: number;
  creada_por_nombre?: string;
  cerrada_en?: string | null;
  cerrada_por?: number | null;
  cerrada_por_nombre?: string | null;
}

export interface FirmaPlanilla {
  id: number;
  version_id: number;
  posicion: number;
  nombre_completo: string;
  cargo: string;
}

/** Respuesta de `GET /api/planillas/versiones/{id}`. */
export interface VersionDetalle {
  version: PlanillaVersion;
  firmas: FirmaPlanilla[];
  lineas: LineaPlanilla[];
}

/** Un cambio de una fila del lote de edición. */
export interface CambioLineaPlanilla {
  detalle_id: number;
  importe: number;
  dias_licencia: number;
  descuentos: Record<string, number>;
  [concepto: string]: number | Record<string, number>;
}

export interface TipoDescuento {
  id: number;
  codigo: string;
  nombre: string;
  orden: number;
  activo: boolean;
  aplica_iiee: boolean;
  aplica_sede: boolean;
}

// ---------------------------------------------------------------------------
// Catálogos
// ---------------------------------------------------------------------------

export interface Nivel {
  id: number;
  nombre: string;
  activo: boolean;
}

export interface Institucion {
  id: number;
  codigo_modular: string;
  nombre: string;
  nivel_id: number;
  nivel_nombre?: string;
  distrito?: string;
  activo: boolean;
}

export interface AreaSede {
  id: number;
  nombre: string;
  meta_id?: number | null;
  meta_codigo?: string | null;
  activo: boolean;
}

export interface Meta {
  id: number;
  codigo: string;
  descripcion: string;
  programa_id?: number | null;
  partida_id?: number | null;
  programa_codigo?: string | null;
  partida_codigo?: string | null;
  activo: boolean;
}

export interface Programa {
  id: number;
  codigo: string;
  nombre: string;
  orden?: number;
  activo: boolean;
}

export interface Partida {
  id: number;
  codigo: string;
  descripcion: string;
  activo: boolean;
}

export interface Cargo {
  id: number;
  nombre: string;
  activo: boolean;
}

export interface Categoria {
  id: number;
  codigo: string;
  descripcion: string;
  activo: boolean;
}

export interface Situacion {
  id: number;
  nombre: string;
  activo: boolean;
}

export interface Subtipo {
  id: number;
  nombre: string;
  activo: boolean;
}

export interface Firma {
  id: number;
  nombre_completo: string;
  cargo: string;
  activo: boolean;
  /** Alias usados por formularios antiguos; el catálogo devuelve `nombre_completo`/`cargo`. */
  nombre_firmante?: string;
  cargo_firmante?: string;
}

export interface CatalogoBundle {
  niveles: Nivel[];
  instituciones: Institucion[];
  areas: AreaSede[];
  metas: Meta[];
  programas?: Programa[];
  partidas?: Partida[];
  cargos: Cargo[];
  categorias: Categoria[];
  situaciones: Situacion[];
  subtipos: Subtipo[];
  firmas: Firma[];
  tipos_descuento?: TipoDescuento[];
}

// ---------------------------------------------------------------------------
// Importaciones
// ---------------------------------------------------------------------------

export interface ImportacionResumen {
  id: number;
  planilla_version_id: number;
  tipo_descuento_id: number;
  archivo_id: number;
  estado: string;
  revision_edicion: number;
  registros_detectados?: number;
  identificados?: number;
  filas_duplicadas?: number;
  registros_rechazados?: number;
  total_detectado?: number;
  tipo_descuento_codigo?: string;
  tipo_descuento_nombre?: string;
  archivo_nombre?: string;
}

export type EstadoFilaImportacion = 'IDENTIFICADO' | 'REVISAR' | 'DNI_DUPLICADO' | 'RECHAZADO';

export interface ImportacionFila {
  id: number;
  importacion_id: number;
  fila: number;
  estado: EstadoFilaImportacion;
  seleccionado: boolean;
  dni_original?: string | null;
  nombre_original?: string | null;
  monto_original?: number | null;
  monto_validado?: number | null;
  observacion?: string | null;
  trabajador_apellidos?: string | null;
  trabajador_nombres?: string | null;
  trabajador_adscripcion?: string | null;
}

/** Respuesta de `GET /api/importaciones/{id}`. */
export interface ImportacionDetalle {
  resumen: ImportacionResumen;
  filas: ImportacionFila[];
}

/** Respuesta de `POST /api/importaciones/procesar`. */
export interface RespuestaProcesarImportacion {
  ok: boolean;
  mensaje: string;
  resumen: {
    importacion_id: number;
    registros_detectados: number;
    identificados: number;
    filas_duplicadas: number;
    registros_rechazados: number;
    total_detectado: number;
  };
}

// ---------------------------------------------------------------------------
// Auditoría
// ---------------------------------------------------------------------------

export interface EventoAuditoria {
  id: number;
  fecha_hora: string;
  usuario_id: number | null;
  usuario_nombre: string | null;
  accion: string;
  entidad: string;
  entidad_id: number | null;
  descripcion: string;
  resultado: 'EXITO' | 'RECHAZADO' | 'ERROR';
  correlacion: string;
  total_cambios: number;
}

export interface CambioAuditoria {
  id: number;
  auditoria_id: number;
  entidad: string;
  entidad_id: number;
  campo: string;
  valor_anterior: string | null;
  valor_nuevo: string | null;
}

/** `GET /api/auditoria` (paginado en el servidor). */
export type PaginaAuditoria = Pagina<EventoAuditoria>;
