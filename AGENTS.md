# Preferencias de trabajo

El propietario solicita mantener GitHub actualizado al finalizar las tareas.

- Tras completar y validar cambios solicitados, crear un commit y hacer push a la rama habitual del repositorio (actualmente `main` en `origin`). Esta publicación está autorizada; no pedir confirmación de nuevo para cada tarea.
- Si una tarea modifica tanto Android como el backend RCA, publicar los cambios correspondientes en ambos repositorios.
- Consultar primero el remoto e integrar cambios nuevos sin sobrescribir trabajo ajeno. No utilizar force push ni descartar cambios locales.
- Publicar código, pruebas y documentación. Excluir secretos, `.env`, claves de firma, entornos virtuales, bases de datos, adjuntos y artefactos de compilación.
- Verificar el resultado del push e informar repositorio, rama y commit. Si GitHub rechaza la operación o no hay conexión, indicar claramente que la publicación sigue pendiente.
- Un push no despliega el servidor. Distinguir la actualización del código mediante `git pull` del reinicio del servicio y de la distribución del APK.
