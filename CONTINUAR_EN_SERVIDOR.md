# Continuidad RCA: pruebas en 192.168.38.14

Preparado el 29 de septiembre de 2026 para retomar desde otro PC con acceso a la red del servidor. Este archivo se publica en la raíz de ambos repositorios y permite continuar sin disponer del historial de la conversación.

## Solicitud del usuario

Revisar y profesionalizar la aplicación Android y su backend, comprender y corregir el proceso completo, y comprobar que ambos funcionan juntos. El usuario se cambia ahora a un PC con acceso a `192.168.38.14` para poder continuar las pruebas reales. Ya autorizó modificar el código de ambos proyectos y solicita **hacer commit y push de los cambios validados al terminar cada tarea**, para actualizar otros equipos mediante Git. Esta preferencia también consta en `AGENTS.md`.

Frase para retomar: **«Revisa CONTINUAR_EN_SERVIDOR.md y continúa las pruebas con el servidor 192.168.38.14».**

## Estado confirmado al dejar esta sesión

- Android: [rgonzalez1043/rca_app](https://github.com/rgonzalez1043/rca_app), rama `main`. Commit de implementación probado: `4efe1c434bc3c54b04c41e4a70705e03aca33fcf`.
- Backend: [rgonzalez1043/RCA_Confiabilidad](https://github.com/rgonzalez1043/RCA_Confiabilidad), rama `main`. Commit de implementación probado: `c9831201f033d603382baa1233b2d764e023f8c2`.
- Ambos commits están publicados y se verificó su coincidencia con GitHub. Los commits posteriores de continuidad/documentación no cambian esa referencia de implementación; consultar `git log` para conocer el último HEAD.
- Rutas encontradas en el PC anterior: Android en `C:\Android Projects\rca_app`; backend en `C:\Python Projects\RCA_Confiabilidad`. El usuario había indicado `C:\Python Projects\RCA\_Confiabilidad`, pero la carpeta real encontrada fue la primera. **Localizar las rutas efectivas en el nuevo PC y en el servidor; no asumir que coinciden.**
- API prevista: `http://192.168.38.14:8007`. Servicio documentado: `RCAService`, Windows/NSSM con Uvicorn. Confirmar puerto, ruta e intérprete del proceso realmente desplegado.
- Validación local completada: `flutter analyze --no-pub` sin incidencias, **40 pruebas Flutter** aprobadas, APK debug compilado y **19 pruebas del backend** aprobadas.
- El backend se probó con SQLite en memoria, JWT de prueba y archivos temporales; no con el MySQL real. Hubo avisos de deprecación de TestClient/httpx, sin fallos de pruebas. No se actualizaron masivamente las dependencias de producción.
- **No se desplegó en el servidor, no se reinició su servicio y no se accedió a su base de datos.** El PC anterior estaba en otra red. La versión que está ejecutándose en `38.14` sigue sin confirmar.
- Logs, APK y copias previas de código quedaron en `build/` del PC anterior y están excluidos de Git. No estarán disponibles por hacer pull en otro PC. El APK se debe reconstruir; la firma de producción y los secretos se conservan por los medios habituales, fuera de Git.

## Sesión del 29/09/2026 en el PC con acceso a la LAN

- PC de desarrollo en la misma LAN. Rutas: backend en `C:\1.-Proyectos\RCA_Confiabilidad`; Android en `C:\3.- Aplicaciones Android\rca_app`. Ambos repositorios estaban limpios y coincidían con `origin/main` antes de empezar.
- Desde este PC solo se consultó la API. El acceso administrativo al servidor se hace por VNC, no por escritorio remoto. No se accedió a la base de datos ni a los archivos del servidor.
- Comprobaciones de solo lectura: `/` y `/openapi.json` informan **1.1.0**; `/health` informa BD conectada. Faltan `/rca/{id}/historial`, `/archivo/{id}/contenido` y DELETE de evidencias. **La versión 1.2.0 sigue sin desplegarse.**
- Revisión del código de ambos proyectos. El esquema 1.2.0 solo añade la tabla `rca_historial`. Las rutas de evidencias de 1.1.0 (`fotos/<nombre>`) siguen siendo compatibles. La actualización no añade dependencias; Pillow ya estaba en `requirements.txt`.
- Correcciones del backend, compatibles con la APK `4efe1c4`:
  1. Reabrir un RCA cerrado desde Android devolvía 409 si el registro tenía espacios sobrantes, como los guardados por la versión 1.1.0. Ahora la comparación ignora esas diferencias; una prueba reproduce el caso.
  2. `fecha_actualizacion` se guardaba en UTC y `fecha_aprobacion` se entregaba en UTC, mientras Android las interpreta como hora local. Esto desplazaba de 3 a 4 horas la fecha del PDF de Android. Ahora ambas usan la hora local, igual que `fecha_creacion`. El historial sigue en UTC porque Android ya lo convierte.
- Backend: **21 pruebas aprobadas**, ejecutadas con Python 3.13 y versiones compatibles en un entorno temporal. Las versiones fijadas requieren Python 3.10–3.12.
- **Paquete ZIP de actualización.** El usuario prefirió llevar un ZIP al servidor y acceder por VNC; RDP no está habilitado. Se añadieron `VERIFICAR_SERVIDOR.bat`, `ACTUALIZAR_SERVIDOR.bat`, `actualizar_servidor.ps1` y `backend/verificar_despliegue.py`. `rca_historial` se crea explícitamente como InnoDB/utf8mb4. El ZIP incluye `versiones_conocidas.txt`, que no está en Git, para detectar cambios locales no publicados.
- **Prueba en un servidor simulado** (MariaDB 10.11 local e instalación 1.1.0 con datos heredados: foto guardada por 1.1.0, RCA cerrado con espacios y contraseña de BD con caracteres especiales):
  - Verificación de solo lectura correcta. Detectó un archivo modificado localmente y un usuario de BD sin permiso CREATE.
  - Ante un fallo simulado del arranque, el script revirtió a 1.1.0 y dejó la API en línea.
  - La actualización a 1.2.0 fue correcta, con respaldo de código, `.env`, adjuntos y `mysqldump`.
  - Integración sobre InnoDB: 20/20 comprobaciones de 1.2.0. Incluyen 5 rondas de guardado simultáneo con la misma revisión (uno 200 y otro 412), la cuota de 10 fotos con 5 cargas simultáneas, la foto y la ruta `/archivos/` heredadas con sesión, la reapertura del cerrado heredado con el cuerpo de Android, el flujo completo, el historial, el PDF y la clave foránea de `rca_historial`.
  - El servicio NSSM se sustituyó por funciones de prueba, porque este PC no tiene permisos de administrador.
- **Hallazgo sobre datos de producción:** la app anterior enviaba `tiempo_parada` y la API 1.1.0 solo aceptaba `tiempo_parada_horas`. Las horas de parada de los RCA existentes no se guardaron y no se pueden recuperar desde el servidor. La versión 1.2.0 acepta ambos nombres.
- **APK:** en este PC se instalaron Flutter 3.38.10, JDK 17 y el Android SDK en el perfil del usuario, sin permisos de administrador. `flutter analyze` no encontró problemas. La compilación y las pruebas fallan porque la política de seguridad del equipo deniega la ejecución de `impellerc.exe`, el compilador de shaders de Flutter; no se intentó eludirla. La APK de prueba se compila en GitHub Actions (`.github/workflows/apk.yml`), que también ejecuta `analyze` y las pruebas. Se descarga desde Actions > ejecución > Artifacts.
- Pendiente: ejecutar el paquete en el servidor real (`INSTRUCCIONES.txt` de la entrega) y las pruebas en la tablet.

## Cambios que hay que validar en conjunto

1. **Contrato de datos.** Horas decimales en `tiempo_parada_horas` con alias `tiempo_parada`; fecha del evento editable; conservación de autoría, acciones, área responsable, categoría, análisis y verificación. Porqués con cinco posiciones, incluidos huecos; `[]` y `{}` borran las herramientas, mientras `null` no las cambia.
2. **Guardado concurrente.** La API devuelve `revision` y ETag. PUT/DELETE de RCA y POST antiguos de herramientas requieren `If-Match: "<revision>"`: 428 si falta y 412 si es antigua. Android conserva el borrador de análisis y detiene los reintentos ante conflicto. MySQL utiliza READ COMMITTED y bloqueo de la fila RCA; falta probar la concurrencia real en InnoDB.
3. **Etapas y permisos.** Activos Mantenedor/Supervisor/Gerente editan; solo Supervisor/Gerente cambia una etapa a la vez: Abierto → En Análisis → En Implementación → Cerrado. Cerrado/Cancelado son de consulta. Reabrir Cerrado lleva a implementación y no permite cambiar contenido en esa misma petición.
4. **Cierre verificable.** Para iniciar análisis: título, falla y criticidad. Para implementar: además, tres primeros porqués consecutivos, dos categorías Ishikawa con causas y causa raíz. Para cerrar: además, acciones correctivas, responsable, compromiso, resultado de efectividad, fecha de verificación no futura y efectividad confirmada.
5. **Historial.** Tabla nueva `rca_historial`, creada al iniciar mediante `create_all()`. No hay ALTER de columnas existentes. `/rca/{id}/historial` registra creación y transiciones, con identidad y fecha del servidor. La aprobación se deriva de la transición a implementación. No se reconstruye historial antiguo ni se audita cada edición.
6. **Evidencias.** Carga 201, nombres UUID, validación real de imágenes, límite por defecto de 10 fotos y 10 MB. Los valores del `.env` existente prevalecen: comprobarlos. Descargas `/archivo/{id}/contenido` y `/archivos/...` requieren sesión; DELETE de archivo implementado. No se permite subir o borrar en cerrados/cancelados.
7. **Autenticación.** Registro HTTP restringido a administrador activo; solo Gerente crea Gerente. `backend/bootstrap_admin.py` es únicamente para instalaciones sin usuarios, no para reinicializar la instalación existente.
8. **Reportes.** Imprimir/compartir en Android usa un informe completo común, con fotos autenticadas y cierre. Una foto fallida impide exportar silenciosamente un informe incompleto. Los documentos adjuntos se enumeran sin incrustar su contenido. El PDF del backend incluye análisis/cierre, no fotos, y se elimina después de enviarse.

## Trabajo pendiente, en orden

### 1. Identificar y comprobar sin modificar datos

Leer `AGENTS.md` y este archivo. Revisar estado, rama y remoto de ambos proyectos; preservar los cambios que existan en el nuevo equipo o servidor. Hacer fetch y comparar antes de integrar. Los cambios del servidor podrían no estar en GitHub.

Desde el PC conectado a la LAN se pueden ejecutar estas comprobaciones de lectura:

```powershell
Test-NetConnection -ComputerName 192.168.38.14 -Port 8007
Invoke-RestMethod -Uri 'http://192.168.38.14:8007/' -TimeoutSec 10
Invoke-RestMethod -Uri 'http://192.168.38.14:8007/health' -TimeoutSec 10
$rcaOpenApi = Invoke-RestMethod -Uri 'http://192.168.38.14:8007/openapi.json' -TimeoutSec 10
$rcaOpenApi.info
```

La revisión nueva declara versión **1.2.0**. Contrastar también rutas/esquemas y el commit desplegado, no solo el número de versión. Si algo falla, distinguir red/puerto, proceso y conexión a BD antes de modificar configuración.

Tener acceso a la LAN no equivale a disponer de una consola del servidor. Confirmar el mecanismo de acceso disponible. Consultar `RCAService`, su ruta NSSM, entorno Python, logs y MySQL **en el servidor real**, no por error en el PC cliente. Leer únicamente la configuración necesaria y no volcar `.env`, tokens o contraseñas al chat ni al repositorio. Usar una cuenta de prueba autorizada; si falta acceso o autenticación, solicitar ese dato concreto sin inventarlo.

### 2. Preparar y aplicar la actualización coordinada si sigue pendiente

Seguir la guía de integración: en Android `docs/INTEGRACION_BACKEND.md`; en backend `INTEGRACION_ANDROID.md`. Complementar con `SERVICIO_WINDOWS.md` del backend. Primero comprobar respaldo vigente de BD/adjuntos/configuración, esquema real, tablas InnoDB, permisos para crear `rca_historial` y qué clientes Android siguen usando la versión antigua.

**Compatibilidad a tener presente:** la API nueva exige revisión para guardar y deja de servir evidencias públicamente. Hay que coordinar backend y APK. Un pull actualiza archivos; no recarga el proceso Uvicorn, no instala el APK ni transfiere las claves de firma.

En la intervención prevista, detener el servicio correcto, actualizar su repositorio con `git pull --ff-only`, mantener `.env`, entorno y datos locales, y volver a iniciarlo. Confirmar la creación de `rca_historial`, `/health` y logs. Si el esquema real difiere del modelo, preparar una migración concreta antes de iniciar: `create_all()` no modifica tablas ya existentes. No configurar `RCA_TESTING=1` en producción. Conservar el commit previo para revertir código si fuera necesario, sin eliminar rutinariamente la tabla de historial.

### 3. Pruebas de integración reales

Usar registros identificables de prueba y cuentas autorizadas; no convertir los casos operativos existentes en datos de ensayo. Las pruebas unitarias bajo `tests/` fuerzan SQLite y **no** comprueban el servidor: no quitar esa protección para ejecutarlas contra la BD real.

- [ ] Login válido/inválido, sesión expirada, usuario inactivo y restricciones por rol.
- [ ] Crear y volver a consultar un RCA; editar horas como 1,5, fecha del evento y acciones; verificar que no desaparezcan campos al guardar.
- [ ] Guardar porqués con huecos, completar los tres primeros, borrar todas las causas y recargar para confirmar persistencia.
- [ ] Rechazar saltos de etapa, cierre incompleto y cambios de estado por Mantenedor; completar el ciclo normal, historial y reapertura como Supervisor/Gerente.
- [ ] Confirmar que la API ignora autoría/aprobaciones falsificadas en el cuerpo y usa la identidad autenticada.
- [ ] Cargar/ver/borrar una foto; probar nombres repetidos, imagen falsa, límite y cuota; rechazar descarga sin sesión y escrituras en cerrados.
- [ ] Dos clientes cargan la misma revisión y guardan cambios distintos: uno guarda y el otro recibe 412 sin sobrescribir. Probar también peticiones simultáneas reales sobre InnoDB y revisar que no haya bloqueos persistentes. Si se prueba el límite simultáneo de fotos, no debe superarse la cuota.
- [ ] Verificar consulta de registros históricos, paginación e indicadores; revisar agregación por área en MySQL.
- [ ] Abrir PDF del backend y generar/compartir el de Android: textos extensos, acentos, fotografías y verificación de cierre. Confirmar limpieza del PDF temporal del servidor.

### 4. Android físico y entrega

- [ ] Compilar con la URL LAN correcta y probar conexión desde el dispositivo. La configuración ya contempla HTTP para `192.168.38.14`; no ampliar excepciones sin necesidad.
- [ ] Cámara/galería, salida inmediata tras escribir, conflicto entre dos dispositivos, cierre/reapertura, historial e impresión/compartir.
- [ ] Comprobar presentación con fuentes grandes y tablet; la generación PDF tiene pruebas estructurales, pero falta su revisión visual final.
- [ ] Revisar `generar-apk-firmado.ps1` y la configuración real de firma para distribuir con la clave habitual. No sustituir esa clave ni publicar contraseñas. Debug no garantiza una actualización sobre una instalación firmada para producción.

## Qué no está resuelto todavía

El token permanece en SharedPreferences y hay HTTP en la LAN. Los borradores son de memoria; no hay sincronización offline ni recuperación de cámara tras terminación del proceso. Faltan acciones estructuradas, una política de cancelación, auditoría de cada edición y paginación visible para grandes volúmenes. No confundir estas mejoras futuras con la verificación inmediata del despliegue. La efectividad de cierre es la declaración registrada por el usuario, no una demostración automática de la solución técnica.

## Cómo cerrar la próxima sesión

Anotar aquí las pruebas realmente realizadas, fecha, versiones/commits desplegados, resultados, IDs de los casos de prueba y asuntos pendientes. No marcar una comprobación como hecha solo porque pasó con SQLite o porque se pudo descargar el código. Publicar los cambios validados en los repositorios afectados, verificar el push y dejar claro qué está en GitHub, qué está desplegado y qué APK fue instalado. No se necesita volver a pedir autorización para los commits/push habituales ya solicitados.
