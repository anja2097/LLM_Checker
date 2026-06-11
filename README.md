# Serial to Parallel Translator

Traductor automático de código C/C++ **serial** a versiones **paralelas** (OpenMP, Kokkos o MPI) mediante modelos de lenguaje accedidos vía [OpenRouter](https://openrouter.ai/). Compila, corrige errores de forma iterativa y verifica que la salida coincida con el programa original.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Dependencias](https://img.shields.io/badge/dependencias-requests-green)
![Estado](https://img.shields.io/badge/estado-activo-brightgreen)

---

## 🖥️ Demo

```bash
cd openmp_translator
python main.py ../OpenMP_intro_tutorial/hello.c -b OpenMP -m qwen3-coder
```

Salida esperada (resumida):

```text
Traduciendo hello.c -> hello_openmp.c
  Backend:    OpenMP
  Modelo:     qwen/qwen3-coder:free

--------------------------------------------------
  Iteración 1 — traducción inicial
--------------------------------------------------
HTTP 200
  Fichero actualizado: .../hello_openmp.c

  Compilando (OpenMP): gcc -O2 -Wall -fopenmp -lm hello_openmp.c -o hello_openmp
  Resultado: compilación OK

Compilado correctamente en la iteración 1.

==================================================
  Verificación: serial vs OpenMP
==================================================
  Salida idéntica (stdout y stderr)
  Speedup: 2.35x
```

---

## ✨ Características principales

- Traduce ficheros `.c` / `.cpp` serial a **OpenMP**, **Kokkos** o **MPI** con un solo comando
- Selección de **modelo LLM** por alias corto o ID completo de OpenRouter
- **Corrección iterativa** automática ante errores de compilación (hasta 5 intentos)
- **Limpieza de respuestas** del LLM (fences markdown, texto explicativo previo al código)
- **Compilación y ejecución** integradas con el toolchain de cada backend
- **Verificación funcional**: compara stdout/stderr del binario serial frente al traducido
- **Benchmark básico** con media de 3 ejecuciones y cálculo de speedup
- **Backends extensibles** mediante carpetas en `prompts/` (descubrimiento automático)

---

## 🛠️ Tecnologías

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.10+ |
| API LLM | OpenRouter (`requests`) |
| Compilación serial / OpenMP | `gcc` / `g++`, OpenMP (`-fopenmp`) |
| Compilación MPI | `mpicc` / `mpicxx` |
| Compilación Kokkos | `g++` + flags desde `.env` o `kokkos_config` |
| Ejecución MPI | `mpirun` |

**Dependencias de producción** (`requirements.txt`):

- `requests>=2.31.0`

**Dependencias de desarrollo**: el proyecto no define un `requirements-dev.txt`; basta con el intérprete Python y las herramientas de compilación del sistema.

---

## 📋 Requisitos previos

### Runtime

- **Python** 3.10 o superior
- **pip** o **uv** para instalar dependencias

### Herramientas del sistema (según backend)

| Backend | Herramientas necesarias |
|---------|-------------------------|
| OpenMP | `gcc` o `g++` con soporte OpenMP |
| MPI | `mpicc` / `mpicxx` y `mpirun` (Open MPI, MPICH, etc.) |
| Kokkos | `g++` (C++20), Kokkos instalado y configurado |

### Cuenta externa

- Cuenta en [OpenRouter](https://openrouter.ai/) con API key válida

---

## 📦 Instalación

1. Clona o copia el directorio del proyecto:

```bash
cd openmp_translator
```

2. Crea y activa un entorno virtual (recomendado):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instala las dependencias Python:

```bash
pip install -r requirements.txt
```

   Alternativa con [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -r requirements.txt
```

4. Copia el fichero de configuración de ejemplo:

```bash
cp .env.example .env
```

5. Edita `.env` y añade tu `OPENROUTER_API_KEY`.

---

## ⚙️ Configuración

Variables de entorno cargadas desde `openmp_translator/.env`:

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `OPENROUTER_API_KEY` | Sí | Clave de API de OpenRouter |
| `MPI_PROCS` | No | Procesos MPI al ejecutar (por defecto: `4`) |
| `KOKKOS_CXX` | No* | Compilador C++ para Kokkos (por defecto: `g++`) |
| `KOKKOS_CXXFLAGS` | No* | Flags de compilación Kokkos |
| `KOKKOS_LDFLAGS` | No* | Flags de enlace Kokkos |

\* Necesarias si compilas con backend Kokkos y no tienes `kokkos_config` en el `PATH`.

Ejemplo de `.env.example`:

```bash
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aqui
MPI_PROCS=4
KOKKOS_CXX=g++
KOKKOS_CXXFLAGS=-std=c++20 -I/usr/local/include -DKokkos_ENABLE_OPENMP
KOKKOS_LDFLAGS=-L/usr/local/lib -lkokkosalgorithms -lkokkoscontainers -lkokkoscore -lkokkossimd -fopenmp -lm
```

Constantes configurables en código (`translator/config/settings.py`):

- `MAX_RETRIES = 5` — iteraciones máximas de corrección
- `BENCHMARK_RUNS = 3` — repeticiones para medir tiempos
- `DEFAULT_MODEL = "qwen3-coder"`
- `DEFAULT_BACKEND_NAME = "OpenMP"`

---

## 🚀 Uso

### Comandos básicos

```bash
# Traducción por defecto (OpenMP + qwen3-coder)
python main.py ruta/al/fichero.c

# Elegir backend y modelo
python main.py ruta/al/fichero.c -b Kokkos -m deepseek-r1
python main.py ruta/al/fichero.c -b MPI -m qwen3-coder
```

### Listar opciones disponibles

```bash
python main.py --list-backends
python main.py --list-models
```

### Reasoning extendido (modelos compatibles)

```bash
python main.py fichero.c -m deepseek-r1 --thinking
python main.py fichero.c -m deepseek-r1 --thinking --thinking-effort high
```

Niveles de esfuerzo: `minimal`, `low`, `medium`, `high`, `xhigh`.

### Referencia de flags CLI

| Flag | Descripción |
|------|-------------|
| `source` | Fichero `.c` o `.cpp` a traducir |
| `-b`, `--backend` | Backend: `OpenMP`, `Kokkos`, `MPI` (por defecto: OpenMP) |
| `-m`, `--model` | Alias de modelo o ID completo de OpenRouter |
| `--list-backends` | Muestra backends y sale |
| `--list-models` | Muestra modelos y sale |
| `--thinking` | Activa reasoning en la API |
| `--no-thinking` | Desactiva reasoning (por defecto) |
| `--thinking-effort` | Nivel de esfuerzo del reasoning (requiere `--thinking`) |

### Ficheros de salida

El traducido se escribe junto al original con el sufijo del backend:

| Entrada | Backend | Salida |
|---------|---------|--------|
| `hello.c` | OpenMP | `hello_openmp.c` |
| `hello.c` | MPI | `hello_mpi.c` |
| `hello.c` | Kokkos | `hello_kokkos.cpp` |
| `pi.cpp` | Kokkos | `pi_kokkos.cpp` |

### Flujo interno

1. Envía el código serial + prompt de traducción al LLM
2. Extrae y limpia el código de la respuesta
3. Compila el fichero traducido
4. Si falla, reenvía errores de compilación al LLM (historial multi-turno)
5. Tras compilar con éxito, ejecuta serial vs traducido y reporta speedup

---

## 📁 Estructura del proyecto

```text
openmp_translator/
├── main.py                      # Punto de entrada CLI
├── requirements.txt             # Dependencias Python
├── .env.example                 # Plantilla de variables de entorno
├── prompts/
│   ├── OpenMP/
│   │   ├── translate.txt        # Prompt de traducción inicial
│   │   └── fix_errors.txt       # Prompt de corrección de errores
│   ├── Kokkos/
│   │   ├── translate.txt
│   │   └── fix_errors.txt
│   └── MPI/
│       ├── translate.txt
│       └── fix_errors.txt
└── translator/
    ├── cli/
    │   └── main.py              # Argumentos y orquestación CLI
    ├── config/
    │   ├── settings.py          # Modelos, constantes, rutas
    │   └── env.py               # Carga de .env
    ├── domain/
    │   └── backend.py           # Entidad Backend y descubrimiento
    ├── services/
    │   └── translate.py         # Pipeline traducción + corrección
    └── infrastructure/
        ├── llm/
        │   └── openrouter.py    # Cliente API, extracción de código
        ├── compilation/
        │   ├── openmp.py        # gcc/g++ + OpenMP
        │   ├── mpi.py           # mpicc/mpicxx
        │   ├── kokkos.py        # g++ + Kokkos
        │   └── common.py        # Utilidades compartidas
        └── execution/
            └── runner.py        # Verificación y benchmark
```

---

## 📜 Scripts disponibles

El proyecto no usa `package.json` ni `Makefile`. Los puntos de entrada son:

| Comando | Descripción |
|---------|-------------|
| `python main.py <fichero> [opciones]` | Ejecuta el traductor con la CLI completa |
| `python main.py --list-backends` | Lista backends detectados en `prompts/` |
| `python main.py --list-models` | Lista alias de modelos configurados |
| `uv run main.py <fichero> [opciones]` | Alternativa si usas uv sin activar el venv |
