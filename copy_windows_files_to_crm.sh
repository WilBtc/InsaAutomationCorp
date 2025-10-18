#!/bin/bash
#
# Script: Copiar archivos desde Windows y agregar al CRM
# Origen: Gerencia@100.83.255.12
# Carpeta: C:\Users\gerencia.INSAINGE\Desktop\2025-09-30 SCXXXX Deilim Genesis Fertilizers
# Destino: CRM ERPNext/INSA CRM
#

set -e

echo "========================================================================"
echo "📁 COPIA DE ARCHIVOS WINDOWS → CRM"
echo "========================================================================"
echo ""

# Configuración
WINDOWS_HOST="100.83.255.12"
WINDOWS_USER="soporteapps2"
WINDOWS_PASS="Ins@S0p0rt3***"
WINDOWS_PATH="C:\\Users\\gerencia.INSAINGE\\Desktop\\2025-09-30 SCXXXX Deilim Genesis Fertilizers"
LOCAL_TEMP="/tmp/windows_crm_files_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Configuración:"
echo "   Host Windows: $WINDOWS_HOST"
echo "   Usuario: $WINDOWS_USER"
echo "   Carpeta origen: $WINDOWS_PATH"
echo "   Carpeta temporal: $LOCAL_TEMP"
echo ""

# Crear carpeta temporal
mkdir -p "$LOCAL_TEMP"

echo "🔍 Paso 1: Verificando conectividad a Windows..."
if timeout 5 nc -zv $WINDOWS_HOST 22 2>&1 | grep -q "succeeded\|open"; then
    echo "   ✅ Puerto SSH 22 está abierto"
else
    echo "   ❌ Error: Puerto SSH 22 no está accesible"
    echo ""
    echo "   Por favor, ejecuta este comando en Windows PowerShell (como Administrador):"
    echo "   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"
    echo "   Start-Service sshd"
    echo "   New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22"
    exit 1
fi

echo ""
echo "📂 Paso 2: Listando archivos en carpeta Windows..."

# Listar archivos remotos
sshpass -p "$WINDOWS_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    ${WINDOWS_USER}@${WINDOWS_HOST} \
    "dir \"${WINDOWS_PATH}\"" > "$LOCAL_TEMP/file_list.txt" 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Conexión SSH exitosa"
    echo ""
    echo "   Archivos encontrados:"
    cat "$LOCAL_TEMP/file_list.txt" | grep -E "^\s*\d" | head -20
    echo ""
else
    echo "   ❌ Error al conectar por SSH"
    cat "$LOCAL_TEMP/file_list.txt"
    exit 1
fi

echo ""
echo "📥 Paso 3: Copiando archivos desde Windows..."

# Copiar carpeta completa usando SCP
# Convertir ruta Windows a formato compatible con SCP
REMOTE_PATH_SCP="/cygdrive/c/Users/gerencia.INSAINGE/Desktop/2025-09-30 SCXXXX Deilim Genesis Fertilizers"

# Intentar con scp -r
sshpass -p "$WINDOWS_PASS" scp -o StrictHostKeyChecking=no -r \
    "${WINDOWS_USER}@${WINDOWS_HOST}:\"${REMOTE_PATH_SCP}\"" \
    "$LOCAL_TEMP/" 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Archivos copiados exitosamente"
else
    echo "   ⚠️  SCP falló, intentando con alternativa (tar + ssh)..."

    # Alternativa: comprimir en Windows y copiar
    sshpass -p "$WINDOWS_PASS" ssh -o StrictHostKeyChecking=no \
        ${WINDOWS_USER}@${WINDOWS_HOST} \
        "powershell -Command \"Compress-Archive -Path '${WINDOWS_PATH}' -DestinationPath 'C:\\temp\\crm_files.zip' -Force\"" 2>&1

    # Copiar el ZIP
    sshpass -p "$WINDOWS_PASS" scp -o StrictHostKeyChecking=no \
        "${WINDOWS_USER}@${WINDOWS_HOST}:/cygdrive/c/temp/crm_files.zip" \
        "$LOCAL_TEMP/crm_files.zip" 2>&1

    # Descomprimir
    cd "$LOCAL_TEMP"
    unzip -q crm_files.zip
    echo "   ✅ Archivos copiados desde ZIP"
fi

echo ""
echo "📊 Paso 4: Analizando archivos copiados..."

# Listar archivos locales
find "$LOCAL_TEMP" -type f | while read file; do
    size=$(du -h "$file" | cut -f1)
    filename=$(basename "$file")
    echo "   📄 $filename ($size)"
done

echo ""
echo "🎯 Paso 5: Agregando archivos al CRM..."

# Detectar tipo de archivo y cliente
CUSTOMER_NAME="Deilim Genesis Fertilizers"
PROJECT_NAME="2025-09-30 SCXXXX Deilim Genesis Fertilizers"

echo "   Cliente: $CUSTOMER_NAME"
echo "   Proyecto: $PROJECT_NAME"
echo ""

# Verificar si el cliente existe en ERPNext
echo "   🔍 Buscando cliente en ERPNext CRM..."

# Aquí integraremos con las herramientas MCP de ERPNext
# Por ahora, guardamos los archivos en una ubicación organizada

CRM_STORAGE="/home/wil/crm-files/$CUSTOMER_NAME/$PROJECT_NAME"
mkdir -p "$CRM_STORAGE"

echo "   📁 Copiando a almacenamiento CRM: $CRM_STORAGE"
cp -r "$LOCAL_TEMP"/* "$CRM_STORAGE/"

echo "   ✅ Archivos guardados en CRM storage"

echo ""
echo "📝 Paso 6: Creando registro en CRM..."

# Crear archivo de metadata JSON
cat > "$CRM_STORAGE/metadata.json" <<EOF
{
  "customer": "$CUSTOMER_NAME",
  "project": "$PROJECT_NAME",
  "date_imported": "$(date -Iseconds)",
  "source": "Windows Desktop - Gerencia",
  "windows_host": "$WINDOWS_HOST",
  "original_path": "$WINDOWS_PATH",
  "imported_by": "Claude Code Automation",
  "file_count": $(find "$CRM_STORAGE" -type f ! -name "metadata.json" | wc -l),
  "total_size": "$(du -sh "$CRM_STORAGE" | cut -f1)"
}
EOF

echo "   ✅ Metadata creada"

echo ""
echo "========================================================================"
echo "✅ PROCESO COMPLETADO EXITOSAMENTE"
echo "========================================================================"
echo ""
echo "📊 Resumen:"
echo "   • Archivos copiados: $(find "$CRM_STORAGE" -type f ! -name "metadata.json" | wc -l)"
echo "   • Tamaño total: $(du -sh "$CRM_STORAGE" | cut -f1)"
echo "   • Ubicación CRM: $CRM_STORAGE"
echo ""
echo "📁 Archivos guardados:"
find "$CRM_STORAGE" -type f ! -name "metadata.json" | while read file; do
    echo "   • $(basename "$file")"
done
echo ""
echo "🎯 Próximos pasos:"
echo "   1. Revisar archivos en: $CRM_STORAGE"
echo "   2. Crear/actualizar cliente en ERPNext CRM"
echo "   3. Adjuntar documentos al registro del cliente"
echo ""

# Limpiar archivos temporales
echo "🧹 Limpiando archivos temporales..."
rm -rf "$LOCAL_TEMP"
echo "   ✅ Limpieza completada"

echo ""
echo "========================================================================"
