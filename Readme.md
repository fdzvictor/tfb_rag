# 🚗 RAG para el Análisis del Mercado de Coches  

## 📌 Descripción del Proyecto  
Este proyecto implementa un sistema **RAG (Retrieval-Augmented Generation)** para la consulta y análisis de datos del mercado automotriz. Utiliza un pipeline **ETL** para extraer información relevante de la web **km77**, almacenando los datos en **Supabase** y mejorando la búsqueda mediante una base de datos **vectorial**.  

🔹 **Principales características:**  
- **Scraping avanzado**: Extracción de datos técnicos y reseñas de coches con `BeautifulSoup` y `requests`.  
- **Pipeline ETL**: Procesamiento, limpieza y almacenamiento estructurado en **PostgreSQL**.  
- **Base vectorial**: Similitud de coseno para mejorar la precisión de búsqueda.  
- **Sistema RAG con LLMs**: Agentes de inteligencia artificial para generar consultas SQL y respuestas interpretadas.  
- **Interfaz en Streamlit**: Interacción amigable con el usuario.  

## 📂 Estructura del Repositorio  

. ├── ETL 
  │  ├ scrapeo_km_77.ipynb # Notebook con el scraping de km77 
  ├── Modelizacion 
  │  ├ RAG call # RAG simple que ejecuta queries SQL directas 
  │  ├ RAG agent # RAG con agentes para mejorar precisión de consultas ´
  │  ├ app.py # Aplicación final del sistema RAG 
  ├── src # Funciones auxiliares y conexión a Supabase 
  ├── .gitignore # Archivos a ignorar en Git 
  └── requirements.txt # Dependencias necesarias

markdown
Copiar
Editar

## 🔍 Diferencias entre RAG Call y RAG Agent  
- **RAG Call**: Implementación sencilla donde el LLM genera y ejecuta queries SQL directamente.  
- **RAG Agent**: Utiliza un **agente intermedio** para refinar las consultas SQL y mejorar la recuperación de información, incluso con variaciones en los nombres de los modelos.  

## ⚙️ Instalación y Configuración  

1️⃣ **Clonar el repositorio:**  
```bash
git clone https://github.com/tuusuario/tu-repositorio.git
cd tu-repositorio
```
2️⃣ Instalar dependencias:

```bash
pip install -r requirements.txt
```
3️⃣ Configurar variables de entorno:
Crea un archivo .env y agrega tus credenciales de Supabase:

```bash
SUPABASE_URL=tu_url
SUPABASE_KEY=tu_api_key
```
4️⃣ Ejecutar la aplicación:

```bash

streamlit run Modelizacion/app.py
```

📊 Funcionalidad del Proyecto
✅ Consulta de información de modelos de coches 📌
✅ Interpretación de consultas imprecisas con NLP 🧠
✅ Generación automática de respuestas con LLMs 🤖
✅ Interfaz gráfica para interacción con usuarios 🎨

📈 Impacto y Aplicaciones
✔️ Facilita la búsqueda de información detallada sobre coches
✔️ Optimiza la toma de decisiones en la industria automotriz
✔️ Permite integrar múltiples fuentes de datos en un solo hub

🚀 Próximos Pasos
🔹 Implementación de memoria en el RAG para mejorar el contexto
🔹 Integración con más fuentes de datos (e.g., DGT, ventas por región)
🔹 Optimización del frontend para una mejor experiencia de usuario

📌 Autor: Víctor Fernández
📌 Tecnologías: Python, Supabase, PostgreSQL, LangChain, Streamlit, LLMs








