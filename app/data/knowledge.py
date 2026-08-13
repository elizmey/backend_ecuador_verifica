"""Base de conocimiento en memoria del verificador.

No usa base de datos: los hechos verificados y las fuentes confiables
viven en este módulo y se consultan únicamente en tiempo de ejecución.
"""

PROJECT_INFO = (
    "VeriIA Ecuador es una plataforma ecuatoriana que combate la desinformación "
    "con verificación asistida por IA, monitoreo de narrativas y herramientas "
    "gratuitas para medios, periodistas y ciudadanía."
)

INITIATIVES = [
    {
        "slug": "redacciones",
        "title": "Redacciones",
        "short": (
            "Agentes de IA para que las redacciones resuman documentos oficiales, "
            "generen contexto y monitoreen fuentes."
        ),
    },
    {
        "slug": "verificacion",
        "title": "Verificación",
        "short": (
            "Herramientas para detectar imágenes, audios y videos manipulados o "
            "generados con inteligencia artificial."
        ),
    },
    {
        "slug": "monitoreo-de-narrativas",
        "title": "Monitoreo de narrativas",
        "short": (
            "Rastreo de contenidos virales, narrativas emergentes y campañas "
            "coordinadas de desinformación."
        ),
    },
    {
        "slug": "alertas-colaborativas",
        "title": "Alertas colaborativas",
        "short": (
            "Intercambio de alertas, verificaciones e información entre medios "
            "en tiempo real."
        ),
    },
    {
        "slug": "analisis-de-propuestas",
        "title": "Análisis de propuestas",
        "short": (
            "Comparación de planes de gobierno y discursos para hacerlos más "
            "comprensibles para la ciudadanía."
        ),
    },
    {
        "slug": "adaptacion-para-medios-locales",
        "title": "Adaptación para medios locales",
        "short": (
            "Contenidos para radios, WhatsApp, lenguas indígenas y formatos accesibles."
        ),
    },
    {
        "slug": "alfabetizacion-mediatica",
        "title": "Alfabetización mediática",
        "short": (
            "Videojuegos, simuladores y experiencias para fortalecer el pensamiento crítico."
        ),
    },
    {
        "slug": "visualizacion-de-datos",
        "title": "Visualización de datos",
        "short": (
            "Recursos para analizar y explicar datos electorales y la circulación "
            "de desinformación."
        ),
    },
    {
        "slug": "agentes-conversacionales",
        "title": "Agentes conversacionales",
        "short": (
            "Respuestas ciudadanas construidas con información oficial y fuentes verificadas."
        ),
    },
    {
        "slug": "fortalecimiento-de-medios-locales",
        "title": "Fortalecimiento de medios locales",
        "short": (
            "Automatización, monitoreo y producción asistida para medios regionales "
            "y comunitarios con recursos limitados."
        ),
    },
]

VERDICTS = {
    "verdadero": {
        "label": "Verdadero",
        "description": "La afirmación es correcta y está respaldada por evidencia.",
    },
    "falso": {
        "label": "Falso",
        "description": "La afirmación es incorrecta y contradice la evidencia disponible.",
    },
    "enganyoso": {
        "label": "Engañoso",
        "description": "La afirmación mezcla datos ciertos con interpretaciones engañosas o fuera de contexto.",
    },
    "sin_evidencia": {
        "label": "Sin evidencia suficiente",
        "description": "No se encontró evidencia clara que respalde o contradiga la afirmación.",
    },
}

KNOWN_CLAIMS = [
    {
        "id": "vacunas-autismo",
        "category": "salud",
        "keywords": ["vacun", "autism"],
        "verdict": "falso",
        "confidence": 0.97,
        "explanation": (
            "Estudios científicos internacionales, incluyendo de la OMS y los CDC, "
            "han descartado de forma contundente cualquier vínculo entre las vacunas "
            "y el autismo. El estudio original que lo sugería fue retractado por fraude."
        ),
        "sources": [
            "Organización Mundial de la Salud (OMS)",
            "CDC — Centros para el Control de Enfermedades",
            "Ministerio de Salud Pública de Ecuador",
        ],
    },
    {
        "id": "5g-coronavirus",
        "category": "salud",
        "keywords": ["5g", "coronavirus", "covid"],
        "verdict": "falso",
        "confidence": 0.96,
        "explanation": (
            "Las redes 5G no transmiten ni propagan el coronavirus. El SARS-CoV-2 se "
            "transmite por gotículas respiratorias. Las ondas de radio no transportan virus."
        ),
        "sources": [
            "Organización Mundial de la Salud (OMS)",
            "Unión Internacional de Telecomunicaciones (UIT)",
            "Agencia de Regulación de Telecomunicaciones (ARCOTEL)",
        ],
    },
    {
        "id": "dioxido-cloro-covid",
        "category": "salud",
        "keywords": ["dioxido de cloro", "clorito", "covid", "cura", "tratamiento"],
        "verdict": "falso",
        "confidence": 0.95,
        "explanation": (
            "El dióxido de cloro es un blanqueador industrial y su ingesta es peligrosa "
            "para la salud. No es un tratamiento contra el COVID-19 ni contra ninguna "
            "enfermedad. Autoridades sanitarias han advertido del riesgo de intoxicación."
        ),
        "sources": [
            "Organización Mundial de la Salud (OMS)",
            "Ministerio de Salud Pública de Ecuador",
            "Agencia Nacional de Regulación, Control y Vigilancia Sanitaria (ARCSA)",
        ],
    },
    {
        "id": "tierra-plana",
        "category": "ciencia",
        "keywords": ["tierra", "plana", "redonda", "esferica"],
        "verdict": "falso",
        "confidence": 0.99,
        "explanation": (
            "La Tierra es un esferoide achatado. La redondez de la Tierra está demostrada "
            "por la evidencia astronómica, los viajes alrededor del mundo, las imágenes "
            "satelitales y la física desde hace más de dos mil años."
        ),
        "sources": [
            "NASA",
            "Real Academia de Ingeniería",
            "Instituto Geográfico Militar de Ecuador",
        ],
    },
    {
        "id": "voto-obligatorio",
        "category": "politica",
        "keywords": ["voto", "obligatorio", "votar"],
        "verdict": "verdadero",
        "confidence": 0.94,
        "explanation": (
            "En Ecuador el voto es obligatorio para las personas entre 18 y 65 años, y "
            "facultativo para menores de 18, mayores de 65, personas en el exterior y "
            "efectivos de las Fuerzas Armadas y Policía Nacional."
        ),
        "sources": [
            "Consejo Nacional Electoral (CNE)",
            "Constitución de la República del Ecuador",
            "Código de la Democracia",
        ],
    },
    {
        "id": "naturaleza-sujeto-derechos",
        "category": "politica",
        "keywords": ["naturaleza", "sujeto de derechos", "constitucion", "pachamama"],
        "verdict": "verdadero",
        "confidence": 0.95,
        "explanation": (
            "La Constitución de Ecuador de 2008 reconoce por primera vez en el mundo a la "
            "naturaleza (Pachamama) como sujeto de derechos, con derecho a que se respete "
            "integralmente su existencia y la regeneración de sus ciclos vitales."
        ),
        "sources": [
            "Asamblea Nacional del Ecuador",
            "Constitución de la República del Ecuador (art. 71)",
            "Corte Constitucional del Ecuador",
        ],
    },
    {
        "id": "migrantes-ayudas",
        "category": "sociedad",
        "keywords": ["migrantes", "venezolanos", "ayuda", "bonos", "extranjeros"],
        "verdict": "enganyoso",
        "confidence": 0.85,
        "explanation": (
            "La afirmación generaliza sin datos: los programas de asistencia social del "
            "Estado ecuatoriano se otorgan a la población en situación de vulnerabilidad "
            "según criterios técnicos y no por nacionalidad. Las cifras deben verificarse "
            "en fuentes oficiales."
        ),
        "sources": [
            "Ministerio de Inclusión Económica y Social (MIES)",
            "Instituto Nacional de Estadística y Censos (INEC)",
            "ACNUR — Agencia de la ONU para los Refugiados",
        ],
    },
    {
        "id": "bono-eliminado",
        "category": "sociedad",
        "keywords": ["bono", "eliminado", "bono de desarrollo humano"],
        "verdict": "falso",
        "confidence": 0.88,
        "explanation": (
            "No existe registro oficial de la eliminación del Bono de Desarrollo Humano. "
            "Se recomienda confirmar cambios en los programas sociales directamente en "
            "el Ministerio de Inclusión Económica y Social (MIES)."
        ),
        "sources": [
            "Ministerio de Inclusión Económica y Social (MIES)",
            "Presidencia de la República del Ecuador",
        ],
    },
    {
        "id": "aborto-legal-ecuador",
        "category": "sociedad",
        "keywords": ["aborto", "legal"],
        "verdict": "enganyoso",
        "confidence": 0.84,
        "explanation": (
            "En Ecuador el aborto no es totalmente legal: está permitido únicamente en "
            "casos específicos (riesgo para la vida o salud de la madre, y en casos de "
            "violación en los supuestos que establece la ley). Generalizar diciendo que "
            "es 'totalmente legal' es engañoso."
        ),
        "sources": [
            "Código Orgánico Integral Penal (COIP)",
            "Corte Constitucional del Ecuador",
            "Ministerio de Salud Pública de Ecuador",
        ],
    },
    {
        "id": "dolarizacion-cambio",
        "category": "economia",
        "keywords": ["dolarizacion", "dolar", "salir del dolar", "desdolarizar", "nueva moneda"],
        "verdict": "falso",
        "confidence": 0.87,
        "explanation": (
            "No existe decisión oficial de abandonar la dolarización ni de emitir una "
            "nueva moneda. Los cambios de régimen monetario son atribución del Estado "
            "y no se han anunciado; estas afirmaciones suelen ser especulativas."
        ),
        "sources": [
            "Banco Central del Ecuador (BCE)",
            "Ministerio de Economía y Finanzas de Ecuador",
            "Presidencia de la República del Ecuador",
        ],
    },
]

TRUSTED_SOURCES = [
    {
        "name": "Confirmado — Ecuador Chequea",
        "domain": "ecuadorchequea.com",
        "url": "https://www.ecuadorchequea.com",
        "category": "verificacion",
    },
    {
        "name": "Presidencia de la República del Ecuador",
        "domain": "presidencia.gob.ec",
        "url": "https://www.presidencia.gob.ec",
        "category": "oficial",
    },
    {
        "name": "Gobierno del Ecuador",
        "domain": "gobiernoec.ec",
        "url": "https://www.gobiernoec.ec",
        "category": "oficial",
    },
    {
        "name": "Ministerio de Salud Pública",
        "domain": "salud.gob.ec",
        "url": "https://www.salud.gob.ec",
        "category": "oficial",
    },
    {
        "name": "Ministerio de Inclusión Económica y Social (MIES)",
        "domain": "inclusion.gob.ec",
        "url": "https://www.inclusion.gob.ec",
        "category": "oficial",
    },
    {
        "name": "Consejo Nacional Electoral (CNE)",
        "domain": "cne.gob.ec",
        "url": "https://www.cne.gob.ec",
        "category": "oficial",
    },
    {
        "name": "Banco Central del Ecuador",
        "domain": "bce.fin.ec",
        "url": "https://www.bce.fin.ec",
        "category": "oficial",
    },
    {
        "name": "Instituto Nacional de Estadística y Censos (INEC)",
        "domain": "ecuadorencifras.gob.ec",
        "url": "https://www.ecuadorencifras.gob.ec",
        "category": "oficial",
    },
    {
        "name": "Registro Civil de Ecuador",
        "domain": "registrocivil.gob.ec",
        "url": "https://www.registrocivil.gob.ec",
        "category": "oficial",
    },
    {
        "name": "Servicio de Rentas Internas (SRI)",
        "domain": "sri.gob.ec",
        "url": "https://www.sri.gob.ec",
        "category": "oficial",
    },
    {
        "name": "ARCOTEL — Telecomunicaciones",
        "domain": "arcotel.gob.ec",
        "url": "https://www.arcotel.gob.ec",
        "category": "oficial",
    },
    {
        "name": "El Comercio",
        "domain": "elcomercio.com",
        "url": "https://www.elcomercio.com",
        "category": "prensa",
    },
    {
        "name": "El Universo",
        "domain": "eluniverso.com",
        "url": "https://www.eluniverso.com",
        "category": "prensa",
    },
    {
        "name": "Primicias",
        "domain": "primicias.ec",
        "url": "https://www.primicias.ec",
        "category": "prensa",
    },
    {
        "name": "GK",
        "domain": "gk.city",
        "url": "https://gk.city",
        "category": "prensa",
    },
    {
        "name": "Organización Mundial de la Salud (OMS)",
        "domain": "who.int",
        "url": "https://www.who.int",
        "category": "internacional",
    },
    {
        "name": "NASA",
        "domain": "nasa.gov",
        "url": "https://www.nasa.gov",
        "category": "internacional",
    },
    {
        "name": "The Times",
        "domain": "thetimes.com",
        "url": "https://www.thetimes.com",
        "category": "prensa_internacional",
    },
    {
        "name": "BBC News",
        "domain": "bbc.com",
        "url": "https://www.bbc.com",
        "category": "prensa_internacional",
    },
    {
        "name": "BBC News",
        "domain": "bbc.co.uk",
        "url": "https://www.bbc.co.uk",
        "category": "prensa_internacional",
    },
    {
        "name": "Reuters",
        "domain": "reuters.com",
        "url": "https://www.reuters.com",
        "category": "prensa_internacional",
    },
    {
        "name": "Associated Press",
        "domain": "apnews.com",
        "url": "https://apnews.com",
        "category": "prensa_internacional",
    },
    {
        "name": "The New York Times",
        "domain": "nytimes.com",
        "url": "https://www.nytimes.com",
        "category": "prensa_internacional",
    },
    {
        "name": "The Guardian",
        "domain": "theguardian.com",
        "url": "https://www.theguardian.com",
        "category": "prensa_internacional",
    },
    {
        "name": "CNN",
        "domain": "cnn.com",
        "url": "https://www.cnn.com",
        "category": "prensa_internacional",
    },
    {
        "name": "France 24",
        "domain": "france24.com",
        "url": "https://www.france24.com",
        "category": "prensa_internacional",
    },
    {
        "name": "Deutsche Welle",
        "domain": "dw.com",
        "url": "https://www.dw.com",
        "category": "prensa_internacional",
    },
]
