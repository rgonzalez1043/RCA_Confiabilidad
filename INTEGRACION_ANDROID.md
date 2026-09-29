# Integración Android y backend RCA — 29/09/2026

El backend real revisado está en `C:\Python Projects\RCA_Confiabilidad` y la aplicación en `C:\Android Projects\rca_app`. La ruta encontrada no contiene la subcarpeta `RCA\_Confiabilidad`. Los cambios se prepararon y probaron localmente; no se desplegaron en `192.168.38.14`, no se reinició su servicio y no se accedió a sus datos. Este equipo está en otra red.

## Contrato que ahora comparten

- Las horas de parada admiten decimales. La API conserva `tiempo_parada_horas` y devuelve también `tiempo_parada` para compatibilidad de lectura; si se reciben ambos, prevalece el primero.
- Crear y editar conserva fecha del evento, acciones, análisis, área responsable, categoría y verificación. Un campo omitido en PUT no cambia; `null` borra valores opcionales. En las herramientas, `null` no cambia y `[]` / `{}` borra. Los porqués conservan sus cinco posiciones, incluidos huecos.
- `revision` identifica la versión devuelta por la API. PUT y DELETE de RCA, así como los POST antiguos de porqués e Ishikawa, exigen `If-Match: "<revision>"`. Falta de versión devuelve 428; versión desactualizada, 412. El cliente detiene reintentos automáticos, conserva su borrador de análisis y permite copiarlo antes de recargar.
- Todas las escrituras del RCA y las evidencias bloquean la fila padre durante la transacción. MySQL debe usar InnoDB; las conexiones usan READ COMMITTED. Las pruebas locales de SQLite comprueban rechazos de revisiones antiguas, pero no prueban bloqueos simultáneos reales en MySQL.
- La identidad del creador, modificador, aprobador y autor de transición proviene de la sesión del servidor. Los metadatos enviados por el cliente no sustituyen esa identidad.
- Activos de rol Mantenedor, Supervisor o Gerente pueden editar. Solo Supervisor o Gerente puede avanzar o retroceder una etapa. Cerrado y Cancelado son de consulta. La reapertura de Cerrado a En Implementación no permite modificar contenido en la misma petición.
- Para iniciar análisis se requiere título, falla y criticidad. Para implementar, además, los tres primeros porqués, dos categorías Ishikawa con causas y causa raíz. Para cerrar se añaden acciones correctivas, responsable, fecha compromiso, resultado de verificación, fecha de verificación no futura y efectividad confirmada.
- `/rca/{id}/historial` expone creación y transiciones con autor, fecha UTC y comentario. La app lo muestra desde el menú del detalle. El historial registra etapas, no cada modificación de contenido. La aprobación vigente se deriva del paso de análisis a implementación; volver a análisis la invalida. No se inventan aprobaciones históricas.
- Solo se pueden eliminar borradores en Abierto sin transiciones ni evidencias; se conserva el historial de casos ya iniciados.
- `/archivo/upload` devuelve 201 y los datos completos del archivo. Nombres UUID evitan sobreescrituras; se validan tamaño, cuota y contenido real de imágenes. Por defecto: 10 fotos por RCA y 10 MB por archivo. Revisar los valores existentes en `.env`, que prevalecen sobre los valores por defecto.
- `/archivo/{id}/contenido` y la ruta antigua `/archivos/...` requieren sesión activa y un registro de archivo existente. Se incluye DELETE de evidencia; cerrados y cancelados rechazan cargas y borrados. Android envía el token solo al origen configurado de su API.
- El PDF de Android es el mismo al imprimir o compartir, incluye verificación y fotos autenticadas. Los documentos que no son imágenes se enumeran como adjuntos sin incorporar su contenido. Si falla una foto, la exportación falla con un mensaje. El PDF del backend incluye datos, análisis y cierre; no incrusta fotos. Los PDFs del backend son temporales y se eliminan después de enviarse.
- El registro de usuarios requiere un administrador activo. Solo Gerente puede crear otro Gerente. Para una instalación sin usuarios existe `backend/bootstrap_admin.py`, interactivo y local.

## Actualización del servidor cuando haya acceso

Esta actualización requiere coordinar API y aplicación: los clientes antiguos no envían revisión y las fotos dejan de ser públicas. La APK nueva requiere este backend para aprovechar todas las garantías.

1. En una ventana de mantenimiento, respaldar la base MySQL, los archivos adjuntos, la configuración y el código vigente. Conservar la clave de firma Android y `SECRET_KEY` del servidor.
2. Verificar que las tablas operativas usan InnoDB, que el esquema corresponde al modelo revisado y que el usuario de servicio tiene permiso para crear la tabla nueva. No ejecutar las pruebas contra una copia de producción conectada a MySQL: la suite ya fuerza SQLite temporal.
3. Detener RCAService en el servidor y, desde su repositorio en la rama `main`, ejecutar `git pull --ff-only`. Mantener su `.env`, entorno Python, carpetas `archivos`, `logs` y `respaldos`. Si Git informa cambios locales o divergencia, resolverlos sin descartar el trabajo del servidor antes de continuar. No copiar el entorno de pruebas ni sustituir configuraciones con las de este PC.
4. Al iniciar, `Base.metadata.create_all()` crea `rca_historial` si falta. No se renombra ni altera ninguna columna existente. Los registros anteriores permanecen y comienzan a acumular historial desde su próxima transición. Si la BD real difiere del modelo, preparar una migración explícita antes de iniciar.
5. Iniciar el servicio y comprobar `/health`, `/openapi.json` y versión 1.2.0. Revisar errores de permisos/esquema en los logs. No definir `RCA_TESTING=1` en un servicio real.
6. Distribuir una compilación de la app con la firma habitual y la URL correcta. El APK debug de la revisión sirve para pruebas; no sustituye una entrega firmada ni garantiza actualización sobre una instalación firmada con otra clave.
7. En un RCA de prueba: crear, editar horas decimales y fecha; guardar porqués con huecos y borrados; subir/ver/borrar una foto; avanzar por las etapas; verificar/cerrar/reabrir; abrir historial; generar y compartir PDF. Abrir el mismo RCA en dos dispositivos y comprobar que el segundo guardado recibe conflicto y no sobrescribe al primero.

Si se debe revertir, detener el servicio y restaurar el código previo con su app compatible. La tabla nueva puede permanecer sin uso para conservar el historial; no borrarla como parte de una reversión rutinaria.

## Sincronización con GitHub

Los proyectos se publican por separado en la rama `main`:

- [Android: rca_app](https://github.com/rgonzalez1043/rca_app).
- [Backend: RCA_Confiabilidad](https://github.com/rgonzalez1043/RCA_Confiabilidad).

En cada carpeta correspondiente, `git pull --ff-only` descarga e incorpora los commits publicados si no hay divergencias. El servicio del backend carga el código al iniciar: después de actualizarlo hay que iniciarlo o reiniciarlo como administrador (`Start-Service RCAService` si se detuvo siguiendo el procedimiento anterior, o `Restart-Service RCAService` para una actualización rutinaria). El pull por sí solo no recarga el proceso. Android requiere compilar y distribuir el APK actualizado.

La preferencia de publicar los cambios validados al terminar cada tarea está registrada en `AGENTS.md` de ambos repositorios. Las credenciales, firmas, bases de datos y carpetas generadas permanecen fuera de los commits.

## Pruebas reproducibles

Android, desde su carpeta:

```powershell
flutter analyze --no-pub
flutter test --no-pub
flutter build apk --debug --no-pub
```

Backend, desde su carpeta, en un entorno de pruebas independiente:

```powershell
py -3.10 -m venv .venv-test
.\.venv-test\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-test\Scripts\python.exe -m pytest tests -q
```

La suite configura SQLite en memoria, una clave JWT de prueba y carpetas temporales antes de importar la aplicación. No carga `.env` ni abre MySQL. Las dependencias de producción permanecen fijadas en `requirements.txt`; no se realizó una actualización masiva del entorno existente.

## Límites de esta validación

Queda por comprobar el despliegue real, la compatibilidad con sus datos históricos, bloqueos concurrentes en MySQL/InnoDB, red/HTTPS, cámara e impresión en un Android físico. Los borradores siguen en memoria y el token en SharedPreferences. No se implementaron sincronización offline, acciones estructuradas, cancelación con motivo ni una auditoría de cada edición. El cierre registra la verificación declarada por el usuario; no demuestra por sí mismo la efectividad técnica de las acciones.

El bloqueo y la recarga de entidades siguen la documentación de [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.with_for_update). El ciclo de inicio se prueba con el contexto de [TestClient de FastAPI](https://fastapi.tiangolo.com/advanced/testing-events/).
