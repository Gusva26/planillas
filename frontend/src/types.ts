export interface User {
  id: number;
  username: string;
  nombre: string;
  rol: 'ADMINISTRADOR' | 'PLANILLAS' | 'CONSULTA';
  debe_cambiar_password: boolean;
}

export interface UserAccount {
  id: number;
  usuario: string;
  nombre_completo: string;
  rol: string;
  activo: boolean;
  debe_cambiar_password: boolean;
  revision: number;
}

export interface DashboardSummary {
  iiee: any;
  sede: any;
  trabajadores_activos: number;
  instituciones_activas: number;
  alertas_neto_negativo: number;
}

export interface Trabajador {
  id: number;
  dni: string;
  apellidos: string;
  nombres: string;
  tipo: 'IIEE' | 'SEDE';
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

export interface PlanillaListItem {
  id: number;
  tipo: 'IIEE' | 'SEDE';
  anio: number;
  mes: number;
  version_id: number;
  version_numero: number;
  version_estado: 'BORRADOR' | 'REVISION' | 'CERRADA';
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
  pichincha: number;
  sullana: number;
  subcafae: number;
  brenta: number;
  sitrase: number;
  fentase: number;
  otros: number;
  total_descuentos: number;
  neto: number;
}

export interface CatalogoBundle {
  niveles: any[];
  instituciones: any[];
  areas: any[];
  metas: any[];
  programas?: any[];
  partidas?: any[];
  cargos: any[];
  categorias: any[];
  situaciones: any[];
  subtipos: any[];
  firmas: any[];
}
