
# PROTOHUMANOS 2D — `protoH.py`

> **Simulación evolutiva 2D de protohumanos que no nacen con conceptos, sino con cuerpo, necesidades, memoria asociativa y capacidad de aprender por experiencia.**
>
> Este proyecto explora una pregunta radical: **¿puede aparecer una proto-creencia funcional de vida, muerte, refugio o autopreservación en agentes que empiezan sin saber nada abstracto?**

---

## Tesis del proyecto, formulada con cuidado

Este repositorio **no afirma** que los agentes sean conscientes, sintientes o vivos en sentido biológico. La posición responsable del proyecto es esta:

> `protoH.py` intenta observar si agentes artificiales mínimos, sin conceptos iniciales, pueden desarrollar **representaciones funcionales** que desde fuera se parezcan a conceptos humanos básicos: refugio, peligro, muerte, agua, comida, herramienta, trampa, grupo, lenguaje primitivo o auto-vida.

La diferencia es fundamental:

| Afirmación | Estado dentro del proyecto |
|---|---|
| “La IA está viva de verdad” | **No demostrado. No se afirma.** |
| “La IA siente miedo real” | **No demostrado. No se afirma.** |
| “El agente puede generar asociaciones tipo `daño ↔ evitar`, `cueva ↔ protección`, `yo ↔ humano`” | **Sí: eso es lo que se intenta medir.** |
| “El agente podría acabar mostrando una proto-creencia funcional de estar vivo” | **Hipótesis experimental. Debe probarse con logs, cerebros y conducta.** |

La frase corta del proyecto sería:

> **No buscamos vender humo diciendo que una IA está viva. Buscamos crear un entorno donde se pueda investigar si una IA mínima puede llegar a comportarse como si hubiera descubierto conceptos de vida, muerte y autopreservación sin que nadie se los programe.**

---

## Pregunta pública para investigadores, programadores y curiosos

Este proyecto invita a la comunidad a intentar demostrar o refutar algo concreto:

> ¿Puede un agente artificial sin lenguaje, sin textos humanos, sin conocimiento heredado y sin conceptos preinstalados desarrollar una red estable de asociaciones que equivalga funcionalmente a “yo soy un ser vulnerable y debo evitar dejar de existir”?

Para que la pregunta sea comprobable, el proyecto exige evidencias exportables:

- registro neuronal del agente (`brain NUMERO`);
- árbol genealógico (`tree NUMERO`);
- logs completos (`export logs` / `export all`);
- investigaciones longitudinales (`investigaciones`, `lineage_watch`);
- clips de conceptos importantes (`clips`, `export clip`, `export clips all`);
- comparación contra controles de laboratorio (`lab faker`, `spawn_nolearn`, `immortal` sin aprendizaje).

---

## Por qué esto puede interesar a la gente

La mayoría de sistemas de IA actuales ya llegan entrenados con cantidades enormes de texto, conceptos humanos y lenguaje. Por eso, si un chatbot dice “estoy vivo”, no sabemos si hay algo detrás o si solo está recombinando frases humanas.

`protoH.py` intenta una vía distinta:

1. Crear agentes extremadamente pobres.
2. Darles un cuerpo simulado.
3. Darles hambre, sed, sueño, dolor, energía y muerte.
4. Darles un mundo hostil con animales, agua, objetos, cuevas y depredadores.
5. No darles conceptos abstractos.
6. Observar si sus experiencias crean asociaciones internas.
7. Auditar esas asociaciones desde fuera.
8. Comparar agentes normales contra controles falsos.
9. Invitar a otros a repetir, romper o mejorar el experimento.

La ambición no es demostrar conciencia humana. La ambición es construir una plataforma casera, auditable y ampliable para estudiar **proto-conceptos emergentes**.

---

## Resumen en una frase

`protoH.py` es un laboratorio de vida artificial en terminal donde humanos primitivos nacen casi en blanco, sobreviven en un mapa 2D, heredan genes pero no recuerdos, y pueden llegar a generar señales auditables de conceptos como refugio, peligro, muerte, herramienta, trampa, proto-lenguaje o auto-vida.

---

## Índice

1. [Qué es este proyecto](#qué-es-este-proyecto)
2. [Idea central](#idea-central)
3. [Por qué existe](#por-qué-existe)
4. [Qué intenta demostrar o explorar](#qué-intenta-demostrar-o-explorar)
5. [Cómo funciona a nivel general](#cómo-funciona-a-nivel-general)
6. [Requisitos](#requisitos)
7. [Instalación](#instalación)
8. [Ejecución rápida](#ejecución-rápida)
9. [Qué ves al arrancar](#qué-ves-al-arrancar)
10. [Mapa, símbolos y entidades](#mapa-símbolos-y-entidades)
11. [Sistema de tiempo](#sistema-de-tiempo)
12. [Humanos: cuerpo, necesidades y acciones](#humanos-cuerpo-necesidades-y-acciones)
13. [Genes y herencia](#genes-y-herencia)
14. [Memoria neuronal asociativa](#memoria-neuronal-asociativa)
15. [Metaobservador y detección conceptual](#metaobservador-y-detección-conceptual)
16. [Investigaciones longitudinales](#investigaciones-longitudinales)
17. [Animales, depredadores y ecología](#animales-depredadores-y-ecología)
18. [Cuevas y refugio](#cuevas-y-refugio)
19. [Objetos, inventario y física simple](#objetos-inventario-y-física-simple)
20. [Comandos completos](#comandos-completos)
21. [Exportaciones](#exportaciones)
22. [Laboratorio](#laboratorio)
23. [Comandos especiales recientes](#comandos-especiales-recientes)
24. [Ejemplos de simulaciones posibles](#ejemplos-de-simulaciones-posibles)
25. [Caso ejemplo: el humano 27 como “superdotado”](#caso-ejemplo-el-humano-27-como-superdotado)
26. [Flujos de uso recomendados](#flujos-de-uso-recomendados)
27. [Estructura interna del código](#estructura-interna-del-código)
28. [Configuración principal](#configuración-principal)
29. [Interpretación de logs y colores](#interpretación-de-logs-y-colores)
30. [Limitaciones conocidas](#limitaciones-conocidas)
31. [Consejos para subirlo a GitHub](#consejos-para-subirlo-a-github)
32. [Roadmap sugerido](#roadmap-sugerido)
33. [Licencia](#licencia)

---

## Qué es este proyecto

`protoH.py` es una simulación experimental en terminal que intenta representar un mundo 2D donde aparecen protohumanos extremadamente simples. Estos humanos no nacen con ideas complejas. No saben qué es una cueva, un refugio, la muerte, el miedo, una trampa, una herramienta, una religión, una ruta ni una estrategia. Nacen con necesidades corporales básicas y con capacidades físicas mínimas: moverse, beber, comer, dormir, atacar, coger objetos, soltar objetos, observar el entorno y reproducirse.

El objetivo no es crear una IA conversacional ni un juego convencional. El objetivo es observar si, mediante experiencia repetida, memoria, supervivencia, dolor, hambre, sed, sueño, relación con otros seres y azar, pueden aparecer patrones que desde fuera parezcan conceptos emergentes.

El programa se ejecuta en terminal y dibuja un mapa ASCII/ANSI en tiempo real. En ese mapa hay humanos, pollos, vacas, T-Rex, semillas, piedras, palos, carne, agua y cuevas. El mundo avanza por ticks. Cada tick representa una unidad de tiempo simulada. Cada 24 ticks pasa un día.

---

## Idea central

La idea principal es esta:

> Un protohumano no nace sabiendo nada abstracto. Solo tiene cuerpo, necesidades, memoria y posibilidad de actuar. Si sobrevive suficiente tiempo, puede empezar a asociar experiencias.

Por ejemplo:

- Si tiene sed y bebe agua, puede reforzar una relación entre `agua` y `sed_baja`.
- Si se acerca a un T-Rex y recibe daño, puede reforzar una relación entre `forma_trex` y `dolor`.
- Si duerme poco y luego golpea más débil, puede reforzar una relación entre `sueño_bajo` y `golpe_debil`.
- Si se queda dentro de una cueva y recibe menos daño o descansa, el Metaobservador puede detectar una hipótesis de `refugio`.
- Si suelta semillas cerca de pollos y luego los pollos se acercan, puede surgir una hipótesis externa de `cebo` o `trampa`.
- Si observa seres que dejan de moverse tras daño o hambre, puede generarse una hipótesis débil de `muerte/no_movimiento`.

La simulación no dice que el humano “entienda” de verdad esos conceptos como una persona moderna. Lo que hace es registrar señales conductuales y asociaciones internas. Después, un Metaobservador externo analiza esas señales y asigna confianza a posibles conceptos.

---

## Por qué existe

Este proyecto nace como un experimento de IA/civilización artificial tipo `WorldBox`, pero centrado en una pregunta más primitiva:

> ¿Cómo podría empezar a formarse algo parecido a conocimiento si una criatura no recibe conceptos preinstalados?

En muchos juegos o simuladores, los personajes ya saben construir, comer correctamente, huir, reproducirse de forma optimizada o usar herramientas. Aquí la gracia está en evitar eso. Los humanos deben empezar casi desde cero.

El proyecto busca observar:

- supervivencia básica;
- emergencia de hábitos;
- diferencias entre humanos por genética;
- linajes con mejores rasgos;
- señales de aprendizaje individual;
- señales de transmisión indirecta por descendencia genética, no por herencia de conceptos;
- detección externa de conceptos;
- falsos positivos del detector;
- fallos físicos o lógicos del mundo;
- historias raras que aparecen por azar.

---

## Qué intenta demostrar o explorar

`protoH.py` no demuestra científicamente la aparición real de consciencia. Tampoco demuestra lenguaje real, religión real ni pensamiento abstracto real. Es una simulación de juguete, pero con una arquitectura bastante rica para explorar comportamientos emergentes.

Lo que sí intenta explorar es:

1. **Emergencia conductual:** si una criatura puede comportarse como si hubiera aprendido algo sin que se le haya programado explícitamente ese concepto.
2. **Asociaciones primitivas:** si la repetición de eventos puede formar conexiones internas auditables.
3. **Selección genética:** si ciertos genes como curiosidad, memoria, asociación o exploración generan humanos más interesantes.
4. **Supervivencia y aprendizaje:** si sobrevivir más tiempo permite acumular experiencias que derivan en patrones más complejos.
5. **Diferencia entre saber y parecer saber:** el programa distingue entre lo que el humano tiene internamente y lo que el Metaobservador interpreta desde fuera.
6. **Falsos positivos:** el laboratorio permite crear humanos inmortales sin aprendizaje para medir si el detector “se emociona” demasiado.
7. **Linajes especiales:** algunos humanos pueden nacer con combinaciones genéticas muy buenas, pareciendo “superdotados” dentro del sistema.

---

## Cómo funciona a nivel general

El programa crea un objeto `World`. Ese mundo contiene:

- una cuadrícula 2D;
- terreno;
- cuevas;
- agua;
- objetos;
- criaturas;
- humanos;
- eventos;
- logs;
- investigaciones;
- banco genético;
- laboratorio;
- Metaobservador.

Cada tick ocurre una secuencia aproximada:

1. El mundo avanza el contador de tiempo.
2. Se actualizan semillas y ecología.
3. Se actualizan animales.
4. Se actualizan depredadores.
5. Se actualizan humanos.
6. Cada humano decide o ejecuta acciones según necesidades, genes, memoria y entorno.
7. Se registran eventos.
8. La memoria neuronal se refuerza o decae.
9. Cada cierto número de ticks, el Metaobservador analiza eventos recientes.
10. Se imprimen o guardan logs relevantes.
11. Si el usuario lo pide, se renderiza, pausa, exporta o inspecciona.

---

## Requisitos

### Requisitos mínimos

- Python 3.10 o superior recomendado.
- Terminal compatible con ANSI.
- macOS o Linux recomendado.

### Librerías

El archivo usa librerías estándar de Python:

- `math`
- `os`
- `random`
- `re`
- `statistics`
- `time`
- `sys`
- `select`
- `pathlib`
- `termios`
- `tty`
- `subprocess`
- `tempfile`
- `shutil`
- `html`
- `dataclasses`
- `typing`

No requiere instalar paquetes externos para funcionar en macOS/Linux.

### Aviso sobre Windows

El script importa `termios` y `tty`, módulos típicos de sistemas Unix. Por eso, en Windows puro puede fallar sin adaptación. Para Windows se recomienda:

- usar WSL;
- o ejecutar en Linux/macOS;
- o adaptar la entrada de teclado a `msvcrt`.

---

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
```

O, si solo tienes el archivo:

```bash
mkdir protoH
cd protoH
cp /ruta/donde/lo/tengas/protoH.py .
```

Opcionalmente, crea un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

No hace falta instalar dependencias externas.

---

## Ejecución rápida

Ejecuta:

```bash
python3 protoH.py
```

También puedes dar permisos de ejecución:

```bash
chmod +x protoH.py
./protoH.py
```

Al arrancar, el programa puede preguntar cuántos humanos iniciales quieres. Puedes dejar el valor por defecto o introducir otro número.

Ejemplo:

```text
Cantidad de humanos iniciales > 2
```

Después verás el mapa y una línea de comandos donde puedes escribir órdenes.

---

## Qué ves al arrancar

La terminal muestra un mundo ASCII con colores ANSI. Arriba o alrededor del mapa aparecen datos del estado de la simulación: día, tick, número de humanos vivos, criaturas, modo automático/manual, velocidad, etc.

La entrada de comandos suele aparecer como:

```text
Comando >
```

Si pulsas `Enter` sin escribir nada, en modo manual avanza 1 tick.

---

## Mapa, símbolos y entidades

Los símbolos principales son:

| Símbolo | Significado |
|---|---|
| `.` | suelo vacío |
| `~` | agua |
| `s` | semilla |
| `/` | palo |
| `o` | piedra |
| `m` | carne |
| `C` | pared física de cueva |
| `E` | entrada lógica de cueva, aunque se renderiza como suelo |
| `I` | interior lógico de cueva, aunque se renderiza como suelo |
| `H` | humano normal |
| `L` | humano de laboratorio |
| `P` | pollo |
| `V` | vaca |
| `T` | T-Rex |

El código diferencia entre lo visual y lo lógico. Por ejemplo, una entrada o interior de cueva puede verse como suelo para que el humano no nazca sabiendo que eso es especial. Sin embargo, internamente el mundo sí sabe que esa celda forma parte de una cueva.

---

## Sistema de tiempo

El tiempo se divide en ticks.

Por defecto:

```python
TICKS_PER_DAY = 24
MAX_TICKS = 100_000
```

Esto significa que 24 ticks equivalen a 1 día simulado.

El Metaobservador no analiza absolutamente todo en cada instante, sino cada cierto número de ticks:

```python
DETECTOR_EVERY_TICKS = 12
```

Así se evita que el análisis sea excesivamente ruidoso.

---

## Humanos: cuerpo, necesidades y acciones

Cada humano tiene estado corporal:

- vida (`hp`);
- hambre;
- sed;
- sueño;
- energía;
- edad;
- inventario;
- memoria;
- genes;
- historial de sueño;
- última acción;
- conceptos detectados por el Metaobservador.

Los humanos pueden:

- moverse;
- beber;
- comer semillas o carne;
- dormir;
- atacar;
- morder;
- coger objetos;
- usar objetos como armas simples;
- soltar semillas;
- reproducirse;
- explorar;
- intentar acciones raras;
- experimentar físicamente con palos, piedras o cuevas;
- morir por hambre, sed, daño, edad u otros factores del mundo.

Lo importante es que esas acciones no equivalen automáticamente a conceptos. Un humano puede entrar en una cueva sin “saber” qué es una cueva. Puede repetir una conducta útil sin que el programa le asigne de inmediato el concepto moderno de refugio.

---

## Genes y herencia

Cada humano tiene genes. Los genes no son ADN real, sino parámetros de comportamiento y supervivencia.

Genes principales:

| Gen | Función aproximada |
|---|---|
| `speed` | velocidad o capacidad de movimiento |
| `strength` | fuerza, daño y capacidad de carga |
| `memory` | tamaño y duración de memoria |
| `curiosity` | tendencia a explorar o probar cosas |
| `sociability` | comodidad cerca de otros humanos |
| `aggression` | tendencia a atacar |
| `association` | capacidad de reforzar conexiones |
| `fertility` | tendencia reproductiva |
| `sleep_need` | necesidad de dormir |
| `energy_efficiency` | eficiencia energética |
| `weirdness` | tendencia a acciones raras o experimentales |
| `exploration_spirit` | impulso de explorar lejos y dispersarse |

Cuando nace un hijo, hereda una mezcla de genes de sus padres con mutación. **No hereda conceptos.** Esto es fundamental.

Un hijo puede heredar alta memoria, curiosidad y asociación, pero no hereda “refugio”, “miedo”, “trampa” ni “muerte”. Si parece desarrollar algo parecido, debe surgir de sus propias experiencias.

---

## Memoria neuronal asociativa

Cada humano tiene una `NeuralMemory`. No es una red neuronal profunda. Es un registro asociativo sencillo compuesto por:

- activaciones;
- conexiones entre nodos;
- decaimiento;
- refuerzo.

Ejemplos de nodos posibles:

- `agua`
- `sed_baja`
- `forma_trex`
- `dolor`
- `cueva_interior`
- `reposo`
- `sueño_bajo`
- `golpe_debil`
- `semilla`
- `pollo_cercano`

Una conexión puede verse así:

```text
agua ↔ sed_baja = +0.42
forma_trex ↔ dolor = +0.67
cueva_interior ↔ reposo = +0.31
```

El comando `brain NUMERO` permite ver estas conexiones en detalle.

---

## Metaobservador y detección conceptual

El Metaobservador es una parte externa del programa. No está dentro de la mente del humano. Su función es mirar eventos, conexiones y secuencias para detectar señales de posibles conceptos.

Puede detectar o investigar señales como:

- agua/sed;
- comida/hambre;
- sueño/fuerza;
- cueva/refugio;
- miedo/peligro;
- muerte/no movimiento;
- cebo/trampa;
- almacenamiento;
- patrones culturales;
- secuencias no clasificadas;
- proto-lenguaje/señales;
- vida/existencia;
- exploración/ruta/distancia.

El Metaobservador asigna porcentajes de confianza. Una señal al 20% no debe interpretarse como descubrimiento fuerte. Una señal al 80–90% puede considerarse más importante, pero sigue siendo una interpretación externa.

---

## Investigaciones longitudinales

Cuando el Metaobservador ve algo raro o potencialmente importante, puede abrir una investigación longitudinal.

Una investigación guarda:

- ID de investigación;
- humano de origen;
- humano observado;
- categoría;
- hipótesis;
- día/tick de inicio;
- duración;
- evidencias a favor;
- evidencias en contra;
- confianza;
- estado;
- si es valiosa o no;
- posible seguimiento por linaje.

Esto permite no depender de un único evento aislado. Por ejemplo, un humano puede hacer algo que parezca “refugio” una vez por azar. Eso no basta. Pero si se repite y mejora su supervivencia, la investigación puede ganar confianza.

---

## Animales, depredadores y ecología

El mundo incluye animales:

### Pollos

- Son pequeños.
- Pueden moverse.
- Pueden servir como alimento potencial.
- Pueden reaccionar a semillas.

### Vacas

- Ocupan más espacio que un pollo.
- Pueden atacar o causar daño.
- Pueden reproducirse.

### T-Rex

- Son depredadores grandes.
- Ocupan varias celdas.
- Tienen radio de agresividad.
- Solo persiguen/atacan si un humano está a una distancia determinada.
- Se reproducen cada cierto número de días.
- Tienen un límite máximo.
- Pueden frustrarse si no logran alcanzar a humanos protegidos durante mucho tiempo.

La ecología animal también intenta evitar que todos los animales se amontonen en un borde del mapa. Hay dispersión y regeneración de semillas para mantener el mundo vivo.

---

## Cuevas y refugio

El mapa contiene cuevas pequeñas y grandes.

Las cuevas tienen:

- paredes físicas (`C`);
- entrada lógica (`E`);
- interior lógico (`I`).

Pero visualmente, `E` e `I` pueden verse como suelo. Esto es intencional: el humano no debe nacer sabiendo que ahí hay un refugio.

Una de las rutas conceptuales más interesantes es observar si un humano aprende que ciertos espacios reducen daño, facilitan descanso o mejoran supervivencia.

Posibles señales:

- entra en cueva tras recibir daño;
- duerme dentro;
- sobrevive más dentro;
- vuelve a entrar en momentos de peligro;
- otros humanos se agrupan cerca;
- depredadores se frustran fuera;
- conexiones `cueva_interior ↔ reposo` o `cueva_interior ↔ menos_daño` crecen.

---

## Objetos, inventario y física simple

Objetos principales:

| Objeto | Símbolo | Uso |
|---|---|---|
| semilla | `s` | comida simple, posible cebo |
| palo | `/` | objeto portable, arma débil |
| piedra | `o` | objeto portable más pesado, arma más fuerte |
| carne | `m` | comida |
| pared de cueva | `C` | obstáculo físico |

Los humanos tienen límite de inventario:

```python
MAX_INVENTORY_ITEMS = 5
ALLOWED_INVENTORY_KINDS = {"seed", "stick", "stone", "meat"}
```

No pueden coger cualquier cosa. No pueden meter paredes en el inventario. No pueden cargar peso infinito. La simulación intenta evitar “magia” y representar restricciones físicas simples.

---

# Comandos completos

Los comandos se escriben en la línea:

```text
Comando >
```

A continuación se describen por grupos.

---

## Comandos de ayuda

### `help`

Muestra ayuda general.

Alias:

```text
help
ayuda
comandos
?
```

### `help sim`

Muestra comandos de simulación.

```text
help sim
ayuda sim
```

### `help export`

Muestra comandos de exportación.

```text
help export
ayuda export
```

### `help humans`

Muestra comandos relacionados con humanos y población.

```text
help humans
help human
help población
help poblacion
```

### `help lab`

Muestra comandos de laboratorio.

```text
help lab
ayuda lab
lab help
```

### `help detector`

Muestra comandos del detector y conceptos.

```text
help detector
help conceptos
```

### `help debug`

Muestra comandos de debug.

```text
help debug
help fallos
```

### `help kill`

Muestra ayuda específica del comando `kill`.

```text
help kill
kill_help
```

---

## Comandos de simulación básica

### `Enter`

Si pulsas Enter sin escribir nada, avanza la simulación manualmente.

```text
Comando >
```

Equivale a avanzar `speed` ticks, normalmente 1.

### `auto`

Activa modo automático.

Alias:

```text
auto
run
play
```

Cuando está activo, el mundo avanza sin tener que pulsar Enter cada vez.

### `pause`

Pausa o reanuda.

Alias:

```text
pause
pausar
```

### `stop`

Vuelve a modo manual.

Alias:

```text
stop
manual
```

### `delay X`

Cambia el tiempo de espera entre ciclos.

Ejemplos:

```text
delay 0.1
delay 0.05
delay 0
```

`delay 0` va lo más rápido posible, salvo limitaciones de render y CPU.

### `speed X`

Cambia cuántos ticks avanza cada ciclo.

Ejemplos:

```text
speed 1
speed 10
speed 100
speed 1000
```

`speed 10` significa que cada ciclo avanza 10 ticks.

### `fast`

Activa o desactiva modo turbo adaptativo.

```text
fast
fast off
turbo
turbo off
```

Cuando está activo, el programa intenta ajustar `delay` y `speed` para maximizar ticks por segundo.

### `q`

Sale del programa.

Alias:

```text
q
quit
salir
exit
```

---

## Comandos de población

### `spawn X`

Crea humanos sin padres.

```text
spawn 5
```

Esto crea 5 humanos nuevos. No heredan conceptos de nadie.

### `spawn X padre1,padre2`

Crea hijos de dos humanos concretos.

```text
spawn 5 9,24
```

Crea 5 hijos de los humanos con número de nacimiento 9 y 24.

Importante:

- heredan genes con mutación;
- no heredan conceptos;
- pueden nacer cerca de sus padres si hay espacio.

### `spawn X best`

Crea humanos usando los mejores genes disponibles.

```text
spawn 20 best
```

El programa busca los mejores humanos vivos por puntuación genética. Si no hay suficientes, puede usar candidatos históricos.

### `spawn X bank`

Crea descendencia usando el banco genético.

Alias relacionados:

```text
spawn 20 bank
spawn 20 elite
spawn 20 preserved
```

Sirve para preservar linajes prometedores.

### `spawn X max`

Crea humanos con genes al máximo útil.

```text
spawn 10 max
```

No nacen con conceptos. Solo tienen genes muy altos.

### `spawnmax X`

Alias para crear humanos de genes máximos.

```text
spawnmax 10
spawn_max 10
spawn100 10
spawn_100 10
maxhumans 10
```

### `spawn_nolearn X`

Crea humanos reales inmortales sin aprendizaje conceptual.

```text
spawn_nolearn 10
spawn_nolearn 10 max
```

Esto sirve para medir falsos positivos del detector. Aunque el humano no pueda aprender conceptos, el detector externo puede registrar señales si interpreta mal una secuencia.

### `auto_spawn_1`

Activa o desactiva el auto-spawn cuando solo queda 1 humano.

```text
auto_spawn_1
```

Si se activa, cuando la población se quede casi extinta, el sistema crea nuevos humanos con mezcla genética diversa.

### `auto_spawn_1 N`

Activa auto-spawn y fija la cantidad.

```text
auto_spawn_1 50
```

### `auto_spawn_1 off`

Desactiva auto-spawn.

```text
auto_spawn_1 off
```

---

## Comandos de mejora/preservación genética

### `boost NUMERO vida CANTIDAD`

Aumenta vida máxima y vida actual.

```text
boost 27 vida 20
```

### `boost NUMERO sed VALOR`

Aumenta resistencia a la sed.

```text
boost 27 sed 1.5
```

### `boost NUMERO hambre VALOR`

Aumenta resistencia al hambre.

```text
boost 27 hambre 1.5
```

### `boost NUMERO vejez VALOR`

Aumenta resistencia a la edad.

```text
boost 27 vejez 1.5
```

### `boost NUMERO all`

Aplica mejora completa.

```text
boost 27 all
```

También registra al humano en el banco genético.

### `preserve NUMERO`

Guarda un humano en el banco genético.

```text
preserve 27
```

Alias:

```text
guardar_genes 27
proteger 27
```

### `gene_bank`

Muestra el banco genético.

Alias:

```text
gene_bank
banco_genes
bank
elite
```

### `best_genes`

Muestra los mejores genes vivos o históricos.

Alias:

```text
best_genes
genes
topgenes
best
```

### `tops`

Muestra rankings.

```text
tops
top
rankings
listas
```

Puedes pedir una categoría:

```text
top curiosidad
top memoria
top exploracion
```

---

## Comandos de análisis conceptual

### `logs`

Muestra conceptos o logs útiles.

Alias:

```text
logs
conceptos
important
importantes
```

### `fallos`

Muestra acciones no previstas o fallos raros.

Alias:

```text
fallos
errores
no_previstos
noprevistos
```

### `todos_logs`

Muestra todo el historial de logs de la sesión.

Alias:

```text
todos_logs
todo
all_logs
alllogs
```

### `valiosos`

Muestra solo reportes realmente valiosos.

Alias:

```text
valiosos
valuable
valuable_logs
logs_valiosos
importantes_valiosos
```

### `investigaciones`

Muestra investigaciones longitudinales.

Alias:

```text
investigaciones
investigations
investigation
invests
```

### `investigaciones_valiosas`

Muestra solo investigaciones valiosas.

Alias:

```text
investigaciones_valiosas
investigaciones utiles
investigaciones_útiles
valuable_investigations
```

### `investigar NUMERO`

Muestra un informe de investigaciones asociadas a un humano.

```text
investigar 27
```

Alias:

```text
investigate 27
```

### `lineage_watch NUMERO`

Muestra seguimiento de linaje.

```text
lineage_watch 27
```

Alias:

```text
lineage watch 27
linaje_watch 27
linaje 27
```

---

## Comandos de cerebro y genealogía

### `brain NUMERO`

Muestra el registro neuronal completo de un humano.

```text
brain 27
```

Alias:

```text
neuronal 27
mente 27
```

Incluye:

- estado del humano;
- genes;
- necesidades;
- inventario;
- conceptos detectados;
- activaciones;
- conexiones;
- eventos importantes;
- motivos por los que el Metaobservador cree que hay señales conceptuales.

### `tree NUMERO`

Muestra árbol genealógico del humano.

```text
tree 27
```

Incluye:

- objetivo;
- ancestros;
- hermanos;
- parejas reproductivas;
- hijos;
- nietos;
- descendientes;
- línea directa principal;
- badges de señales importantes.

---

## Comandos de inmortalidad

### `immortal NUMERO`

Marca a un humano como inmortal.

```text
immortal 27
```

Alias:

```text
inmortal 27
```

La inmortalidad es una herramienta experimental. Sirve para pruebas de laboratorio/debug, no para simular evolución natural.

### `mortal NUMERO`

Quita la inmortalidad.

```text
mortal 27
```

Alias:

```text
noimmortal 27
no_inmortal 27
```

### Spawns con inmortalidad

El código también intercepta peticiones donde aparece `immortal` o `inmortal` dentro de comandos de creación. Esto permite crear humanos de prueba protegidos.

Ejemplos conceptuales:

```text
spawn 10 immortal
spawn 10 max immortal
lab spawn 5 immortal
lab bugs 3 immortal
```

En humanos inmortales sin aprendizaje, el detector puede seguir midiendo falsos positivos.

---

# Exportaciones

Las exportaciones permiten sacar información a `.txt`, `.svg`, `.png` o `.html` según el caso.

## Exportación de logs

### `export_logs RUTA`

```text
export_logs ./exports/logs.txt
```

Alias:

```text
exportar_logs ./exports/logs.txt
export logs ./exports/logs.txt
```

Exporta todos los logs de la sesión.

---

## Exportación de conceptos

### `export conceptos RUTA`

```text
export conceptos ./exports/conceptos.txt
```

Exporta reportes conceptuales.

---

## Exportación de fallos

### `export fallos RUTA`

```text
export fallos ./exports/fallos.txt
```

Exporta acciones no previstas/fallos raros.

---

## Exportación útil

### `export useful RUTA`

```text
export useful ./exports/protoH_util.txt
```

Alias:

```text
export util ./exports/protoH_util.txt
export_valiosos ./exports/protoH_util.txt
export important ./exports/protoH_util.txt
```

Esta es una de las exportaciones más recomendables porque resume lo importante:

- resumen evolutivo;
- reportes valiosos;
- investigaciones;
- banco genético;
- rankings;
- señales destacadas.

---

## Exportación absoluta

### `export all RUTA`

```text
export all ./exports/protoH_TODO.txt
```

Alias:

```text
export_todo ./exports/protoH_TODO.txt
export absoluto ./exports/protoH_TODO.txt
export everything ./exports/protoH_TODO.txt
```

Exporta una cantidad muy grande de información.

Úsalo cuando quieras guardar toda la sesión para analizarla después.

---

## Exportación de investigaciones

### `export investigations RUTA`

```text
export investigations ./exports/investigaciones.txt
```

Alias:

```text
export investigaciones ./exports/investigaciones.txt
```

---

## Exportación de linaje

### `export lineage NUMERO RUTA`

```text
export lineage 27 ./exports/linaje_27.txt
```

Alias:

```text
export linaje 27 ./exports/linaje_27.txt
```

---

## Exportación de cerebro

### `export brain NUMERO RUTA`

```text
export brain 27 ./exports/brain_27.txt
```

Alias:

```text
export_brain 27 ./exports/brain_27.txt
```

---

## Exportación de cerebros de todos

```text
export brains all ./exports/brains/
```

Genera informes neuronales de todos los humanos.

---

## Exportación de árbol

### `export tree NUMERO RUTA`

```text
export tree 27 ./exports/tree_27.svg
```

También puede exportar en `.png` si el sistema lo permite.

### `export tree all RUTA`

```text
export tree all ./exports/tree_all.svg
```

Exporta árbol general.

### `export trees all RUTA_CARPETA`

```text
export trees all ./exports/trees/
```

Exporta árboles individuales y globales.

---

## Exportación de laboratorio

### `export lab RUTA`

```text
export lab ./exports/lab.txt
```

### `export lab all RUTA_CARPETA`

```text
export lab all ./exports/lab_pack/
```

Exporta informe de laboratorio, cerebros y árboles de sujetos LAB.

---

## Exportación de vida externa / auto-vida

### `export auto_life RUTA`

```text
export auto_life ./exports/auto_life.txt
```

Alias:

```text
export autovida ./exports/auto_life.txt
export vida ./exports/auto_life.txt
```

---

## Exportación de métricas del detector

### `export detector_metrics RUTA`

```text
export detector_metrics ./exports/detector_metrics.txt
```

Alias:

```text
export metricas_detector ./exports/detector_metrics.txt
export métricas_detector ./exports/detector_metrics.txt
```

---

## Exportación de proto-lenguaje

### `export lenguaje RUTA`

```text
export lenguaje ./exports/lenguaje.txt
```

Alias:

```text
export proto_lenguaje ./exports/lenguaje.txt
export language ./exports/language.txt
```

---

## Exportación de estadísticas de semillas

### `export seed_stats RUTA`

```text
export seed_stats ./exports/seed_stats.txt
```

Alias:

```text
export semillas ./exports/semillas.txt
```

---

## Exportación de clips

### `export clip N RUTA`

```text
export clip 3 ./exports/clip_3.html
export clip 3 ./exports/clip_3.txt
```

Si la ruta termina en `.txt`, exporta texto. Si no, exporta HTML.

### `export clips all RUTA_CARPETA`

```text
export clips all ./exports/clips/
```

Exporta todos los clips conceptuales.

---

# Laboratorio

El laboratorio permite crear humanos especiales para probar hipótesis sin contaminar del todo la simulación principal.

Los humanos LAB suelen aparecer como `L`.

## Principios del laboratorio

- Un LAB no representa necesariamente un humano natural.
- Puede tener genes ajustados para observar una ruta conceptual.
- No nace sabiendo conceptos.
- Sirve para medir detectores, falsos positivos y fallos.
- Puede estar aislado reproductivamente.
- Puede ser inmortal para pruebas.

---

## Comandos LAB básicos

### `lab`

Muestra ayuda de laboratorio.

```text
lab
lab help
help lab
```

### `lab spawn X`

Crea humanos de laboratorio normales.

```text
lab spawn 5
```

### `lab spawn X max`

Crea humanos LAB con genes máximos útiles.

```text
lab spawn 5 max
```

### `lab spawn X concept CONCEPTO`

Crea humanos LAB orientados a una ruta conceptual.

```text
lab spawn 5 concept refugio
lab spawn 5 concept muerte
lab spawn 5 concept trampa
lab spawn 5 concept distancia
```

Importante: `lab spawn 5 concept refugio` no significa que nazcan sabiendo refugio. Significa que sus genes/perfil y la observación externa están orientados a estudiar esa ruta.

---

## Conceptos orientativos de LAB

Puedes probar focos como:

```text
vida
muerte
miedo
refugio
agua
comida
trampa
almacenamiento
distancia
dimension
social
herramienta
sueño_fuerza
```

---

## `lab list`

Lista sujetos de laboratorio.

```text
lab list
```

Muestra:

- número de nacimiento;
- estado;
- si es inmortal;
- foco;
- score genético;
- posición;
- hijos;
- conceptos detectados.

---

## `lab watch NUMERO`

Muestra detalle de un sujeto LAB o humano observado.

```text
lab watch 27
```

Incluye:

- investigaciones relacionadas;
- evidencias;
- conexiones principales;
- eventos recientes.

---

## `lab watch concept CONCEPTO`

Muestra sujetos LAB de un concepto.

```text
lab watch concept refugio
```

---

## `lab report`

Muestra resumen general del laboratorio.

```text
lab report
```

---

## `lab clear`

Marca como muertos los LAB vivos.

```text
lab clear
```

Sirve para limpiar pruebas.

---

## `lab isolate on/off`

Controla aislamiento reproductivo.

```text
lab isolate on
lab isolate off
```

Con aislamiento activo, los LAB no contaminan la población normal.

---

## LAB avanzado

### `lab detector X CONCEPTO`

Crea sujetos para poner a prueba el detector.

```text
lab detector 5 distancia
lab detector 5 refugio
```

### `lab bugs X`

Crea bug hunters.

```text
lab bugs 5
```

Estos sujetos realizan pruebas para buscar fallos físicos/lógicos.

Pruebas posibles:

- combinar objetos;
- mover cueva;
- golpear aire;
- coger objeto pesado;
- ruta borde;
- apilar piedras;
- soltar/recoger repetido.

### `lab faker X all`

Crea sujetos que simulan descubrimientos falsos para auditar el detector.

```text
lab faker 3 all
```

### `lab faker X vida,refugio`

```text
lab faker 2 vida,refugio
```

### `lab fake_report`

Muestra informe de falsos descubrimientos.

Alias:

```text
lab fakereport
lab audit
lab auditoria
lab auditoría
```

---

# Comandos especiales recientes

## Auto-vida / candidatos de vida externa

### `auto_vida`

Muestra candidatos de vida externa o señales de vida.

Alias:

```text
auto_vida
autovida
vida
life
life_candidates
candidatos_vida
```

Este informe intenta identificar entidades/señales que podrían interpretarse como vida o agencia desde fuera.

---

## Métricas del detector

### `detector_metrics`

Muestra métricas del detector.

Alias:

```text
detector_metrics
metricas_detector
métricas_detector
detector v2
detector_v22
```

Sirve para medir rendimiento, señales, ruido y falsos positivos.

---

## Proto-lenguaje / señales

### `lenguaje`

Muestra informe de proto-lenguaje.

Alias:

```text
lenguaje
proto_lenguaje
language
proto_language
señales
senales
```

Este sistema intenta detectar señales repetidas, patrones sociales o comunicación primitiva.

---

## Estadísticas de semillas

### `seed_stats`

Muestra estadísticas de semillas.

Alias:

```text
seed_stats
semillas
seedmap
seed_stats_v231
```

Útil para entender si la comida vegetal está bien repartida o si el mapa está generando acumulaciones raras.

---

## Kill externo

### `kill ESPECIE CANTIDAD`

Elimina criaturas/humanos externamente.

```text
kill t-rex 5
kill trex all
kill cow 20
kill chicken 10
kill human 3
kill lab all
kill all all
```

Es una intervención externa de laboratorio. Sirve para controlar poblaciones o limpiar pruebas. No representa una acción aprendida por los humanos.

---

## Errores brutos

### `error`

Muestra errores registrados sin cerrar el programa.

Alias:

```text
error
errors
errores
errores_brutos
```

### `error last`

Muestra el último error.

```text
error last
```

### `error ID`

Muestra un traceback concreto.

```text
error 3
```

El sistema captura errores en comandos y ciertos avances para evitar que una excepción mate toda la simulación.

---

## Concept clips

Los clips conceptuales son fragmentos importantes de una simulación que pueden revisarse después.

### `clips`

Lista clips.

Alias:

```text
clips
concept_clips
clip list
clips list
```

### `clips on`

Activa clips.

```text
clips on
clip on
```

### `clips off`

Desactiva clips.

```text
clips off
clip off
```

### `play clip N`

Abre un clip en HTML temporal si el sistema puede.

```text
play clip 3
clip play 3
clip 3
```

### `clip settings`

Muestra configuración de clips.

```text
clip settings
```

---

# Ejemplos de simulaciones posibles

## Ejemplo 1: humano aprende agua/sed

Secuencia posible:

1. Humano nace con sed baja/moderada.
2. La sed aumenta.
3. Se mueve buscando agua.
4. Encuentra `~`.
5. Bebe.
6. Baja la sed.
7. Se registra evento `beber`.
8. Se refuerza conexión `agua ↔ sed_baja`.
9. El Metaobservador puede detectar relación agua/sed.

Posible interpretación:

```text
H#12 muestra señales de asociación agua/sed con confianza 62%.
```

Esto no significa que el humano entienda “agua” como concepto moderno. Significa que su memoria y conducta sugieren una relación práctica.

---

## Ejemplo 2: humano teme a T-Rex

Secuencia posible:

1. Humano explora.
2. Se acerca a un T-Rex.
3. El T-Rex entra en radio de agresividad.
4. Ataca.
5. Humano recibe daño.
6. El humano sobrevive.
7. Más adelante evita una forma parecida o se aleja.
8. Se refuerzan conexiones `forma_trex ↔ dolor` y posiblemente `forma_grande ↔ peligro`.
9. El Metaobservador abre investigación de miedo/peligro.

Posible resultado:

```text
INV17 H34 miedo_muerte confianza 71% estado=OBSERVACIÓN FUERTE
```

---

## Ejemplo 3: proto-refugio en cueva

Secuencia posible:

1. Humano recibe daño fuera.
2. Se mueve por azar hacia una cueva.
3. Entra en interior lógico.
4. Duerme o descansa.
5. Sobrevive mientras depredador no puede alcanzarlo.
6. Repite la conducta.
7. Se refuerza `cueva_interior ↔ reposo` o `cueva_interior ↔ menos_daño`.
8. El Metaobservador detecta hipótesis de refugio.

Posible resultado:

```text
CONCEPTO: posible refugio/cueva
CONFIANZA: 68%
IMPORTANCIA: ALTO
```

---

## Ejemplo 4: cebo con semillas y pollos

Secuencia posible:

1. Humano lleva semillas.
2. Suelta semillas cerca de pollos.
3. Pollos se acercan.
4. Humano ataca o se aproxima.
5. El patrón se repite.
6. Se refuerzan conexiones `semilla ↔ pollo_cercano`.
7. El Metaobservador investiga cebo/trampa.

Posible resultado:

```text
BOT INVESTIGADOR: señal clara encontrada: sí
Hipótesis: posible cebo/trampa con semillas y animales
Confianza: 55%
```

---

## Ejemplo 5: almacenamiento de comida

Secuencia posible:

1. Humano recoge carne o semillas.
2. No las consume inmediatamente.
3. Las transporta.
4. Las deja cerca de una zona recurrente.
5. Más tarde vuelve y come.
6. El Metaobservador detecta posible almacenamiento.

Posible resultado:

```text
Concepto posible: almacenamiento/provisiones
Confianza: 41%
```

---

## Ejemplo 6: sueño y fuerza

Secuencia posible:

1. Humano duerme poco.
2. Ataca o intenta golpear.
3. Hace menos daño.
4. Duerme lo suficiente.
5. Más tarde golpea mejor.
6. Se refuerzan conexiones `sueño_bajo ↔ golpe_debil` y `descanso_suficiente ↔ golpe_fuerte`.
7. El detector puede investigar sueño/fuerza.

---

## Ejemplo 7: proto-lenguaje

Secuencia posible:

1. Varios humanos coinciden cerca.
2. Reaccionan de forma repetida a presencia, comida, peligro o refugio.
3. Se generan señales o patrones sociales.
4. El sistema de lenguaje detecta repeticiones.
5. `lenguaje` muestra informe.

No significa lenguaje humano real. Significa señal social repetible o patrón primitivo.

---

# Caso ejemplo: el humano 27 como “superdotado”

En una simulación puede nacer un humano como el `#27` con una combinación genética excepcional.

Por ejemplo:

- mucha curiosidad;
- mucha memoria;
- alta asociación;
- buen espíritu explorador;
- eficiencia energética alta;
- suficiente fuerza;
- tendencia a acciones raras controladas.

Ese humano puede parecer “superdotado” porque:

1. explora más;
2. sobrevive más situaciones;
3. prueba más cosas;
4. acumula más eventos;
5. forma más conexiones;
6. genera más investigaciones;
7. deja descendencia interesante.

Para analizarlo:

```text
brain 27
```

Mira:

- conexiones principales;
- conceptos detectados;
- eventos crudos;
- relación sueño/fuerza;
- relación agua/sed;
- relación depredador/dolor;
- relaciones con cuevas;
- inventario y objetos.

Después:

```text
tree 27
```

Para ver su familia.

Luego:

```text
lineage_watch 27
```

Para ver si sus hijos o nietos mantienen rasgos interesantes.

Si es realmente valioso:

```text
preserve 27
```

Y puedes crear descendencia:

```text
spawn 20 27,OTRO
spawn 20 best
spawn 20 bank
```

Importante: aunque el humano 27 sea excepcional, sus hijos no heredan conceptos. Heredan potencial.

---

# Flujos de uso recomendados

## Flujo 1: simulación normal

```text
python3 protoH.py
```

Dentro:

```text
auto
```

Deja correr. Luego consulta:

```text
logs
valiosos
best_genes
investigaciones
```

Si aparece alguien interesante:

```text
brain 27
tree 27
lineage_watch 27
preserve 27
```

Exporta:

```text
export useful ./exports/util.txt
```

---

## Flujo 2: buscar humanos excepcionales

```text
auto
speed 100
fast
```

Después:

```text
best_genes
tops
valiosos
gene_bank
```

Si quedan pocos humanos:

```text
auto_spawn_1 50
```

---

## Flujo 3: estudiar refugio

```text
lab spawn 10 concept refugio
lab watch concept refugio
auto
```

Después de unos días:

```text
lab watch concept refugio
investigaciones_valiosas
export lab ./exports/lab_refugio.txt
```

---

## Flujo 4: medir falsos positivos

```text
spawn_nolearn 20 max
detector_metrics
auto
```

Luego:

```text
detector_metrics
valiosos
fallos
```

Si aparecen conceptos fuertes en humanos sin aprendizaje, puede haber falsos positivos.

---

## Flujo 5: depurar fallos

```text
lab bugs 10
lab fake_report
fallos
error
```

Exporta:

```text
export fallos ./exports/fallos.txt
export detector_metrics ./exports/metricas.txt
```

---

## Flujo 6: guardar todo antes de cerrar

```text
export useful ./exports/protoH_util.txt
export all ./exports/protoH_TODO.txt
export clips all ./exports/clips/
```

---

# Estructura interna del código

El archivo está organizado en bloques grandes.

## Configuración

Define tamaño del mapa, población inicial, ticks por día, límites de logs, reproducción de T-Rex, dispersión animal, semillas y opciones generales.

## Símbolos y color

Define caracteres del mapa y colores ANSI.

## Eventos y memoria

Define `Event` y `NeuralMemory`.

## Objetos

Define `Item` y prototipos de objetos.

## Criaturas

Define `Creature`, `Genes` y `Human`.

## Investigaciones

Define `ConceptInvestigation`.

## Mundo

La clase `World` contiene la mayor parte de la simulación:

- creación del mapa;
- spawn inicial;
- movimiento;
- animales;
- humanos;
- combate;
- reproducción;
- logs;
- exportaciones;
- genealogía;
- laboratorio;
- render.

## MetaObserver

Analiza eventos y conexiones para detectar conceptos.

Funciones de detección destacadas:

- `detect_bait_trap`
- `detect_sleep_strength`
- `detect_cave_safety`
- `detect_big_creature_avoidance`
- `detect_fear_or_death_concepts`
- `detect_unclassified_clusters`
- `detect_inventory_storage`
- `detect_cultural_patterns`

## Comandos

La función `process_command` se va ampliando a lo largo del archivo con wrappers sucesivos. Esto permite añadir comandos nuevos sin reescribir todo el bloque original, aunque a largo plazo convendría refactorizarlo a un dispatcher central.

---

# Configuración principal

Valores importantes actuales:

```python
WIDTH = 135
HEIGHT = 28
INITIAL_HUMANS = 2
INITIAL_CHICKENS = 20
INITIAL_COWS = 10
INITIAL_TREX = 2
MAX_TREX = 7
INITIAL_SEED_PATCHES = 80
INITIAL_STICKS = 30
INITIAL_STONES = 25
INITIAL_WATER_PATCHES = 10
TICKS_PER_DAY = 24
MAX_TICKS = 100_000
DETECTOR_EVERY_TICKS = 12
RENDER_EVERY_TICKS = 1
LOG_LIMIT = 900
HUMAN_MEMORY_LIMIT = 700
TREX_REPRODUCE_EVERY_DAYS = 10
TREX_AGGRO_RADIUS = 3.0
MAX_INVENTORY_ITEMS = 5
```

Puedes editar estos valores al principio del archivo.

---

# Interpretación de logs y colores

El sistema clasifica reportes por importancia.

Colores aproximados:

| Color | Significado aproximado |
|---|---|
| rojo | fallo/no previsto/alerta |
| cian | detector/concepto/hipótesis |
| dorado | señal relevante con confianza razonable |
| morado | señal muy fuerte |
| azul oscuro | conclusión clara de investigador/revisor |

El color no convierte una hipótesis en verdad. Solo ayuda a leer.

---

# Limitaciones conocidas

## No es consciencia real

El programa puede generar señales que parecen conceptos, pero no prueba consciencia.

## El Metaobservador puede equivocarse

Puede haber falsos positivos. Por eso existen laboratorio, faker, métricas y humanos sin aprendizaje.

## El código es monolítico

Todo está en un archivo enorme. Funciona como prototipo, pero no es ideal para mantenimiento.

## Los comandos están parcheados por capas

`process_command` se redefine varias veces. Esto permitió evolucionar rápido, pero sería mejor migrar a un sistema modular.

## La simulación depende mucho de parámetros

Pequeños cambios en hambre, sed, depredadores, semillas o genes pueden cambiar mucho los resultados.

## Terminal y rendimiento

Renderizar muchos ticks en terminal puede ser lento. Usa `speed`, `delay` y `fast`.

---

# Consejos para subirlo a GitHub

## Archivos recomendados

Estructura mínima:

```text
protoH/
├── protoH.py
├── README.md
├── LICENSE
└── .gitignore
```

## `.gitignore` sugerido

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
venv/
.env

# macOS
.DS_Store

# Exports generated by protoH
exports/
protoH_logs_*.txt
protoH_TODO*.txt
protoH_util*.txt
protoH_brain_*.txt
protoH_tree_*.svg
protoH_tree_*.png
protoH_clip_*.html

# IDE
.vscode/
.idea/
```

## Nombre de repositorio sugerido

- `protoH`
- `protohumanos-2d`
- `protohumanos-emergence-sim`
- `protoH-2D-evolution-simulator`

## Descripción corta para GitHub

> Experimento de vida artificial donde protohumanos nacen sin conceptos y un detector rastrea ideas aprendidas como refugio, peligro, muerte y auto-vida, con el objetivo de explorar si alguno puede desarrollar una proto-creencia funcional de estar vivo.

## Topics sugeridos

```text
python
simulation
artificial-life
evolution
emergent-behavior
cellular-world
ascii-art
terminal-game
agent-based-model
protohumans
```

---

# Roadmap sugerido

Ideas para futuras versiones:

## 1. Modularizar el código

Separar en archivos:

```text
protoh/
├── main.py
├── world.py
├── human.py
├── animals.py
├── genes.py
├── memory.py
├── metaobserver.py
├── commands.py
├── export.py
├── lab.py
└── render.py
```

## 2. Guardar/cargar simulaciones

Añadir:

```text
save ./saves/run1.json
load ./saves/run1.json
```

## 3. Mejorar lenguaje emergente

Crear señales entre humanos:

- llamada de peligro;
- llamada de comida;
- llamada de refugio;
- imitación;
- aprendizaje social.

## 4. Construcción real progresiva

Permitir que, tras suficientes experiencias, puedan:

- apilar piedras;
- mover palos;
- crear barreras;
- crear chozas;
- marcar caminos;
- guardar comida.

## 5. Estaciones y clima

Añadir:

- lluvia;
- tormentas;
- sequías;
- frío/calor;
- estaciones;
- incendios;
- inundaciones;
- terremotos.

## 6. Civilización generacional

Permitir transmisión cultural real:

- imitación;
- enseñanza;
- señales;
- proto-lenguaje;
- roles;
- cuidado de crías;
- entierros/rituales;
- agricultura;
- domesticación.

## 7. Visualizador externo

Crear una interfaz web o pygame para ver:

- mapa;
- líneas de movimiento;
- árbol familiar;
- conexiones neuronales;
- clips conceptuales;
- evolución por días.

---

# Licencia

Este proyecto se distribuye bajo la **Apache License 2.0**.

Copyright 2026 **YJNWI**.

La Apache License 2.0 permite que otras personas puedan:

- usar el proyecto;
- estudiarlo;
- modificarlo;
- hacer forks;
- redistribuirlo;
- incluirlo en otros proyectos;
- usarlo comercialmente;
- vender copias modificadas o sin modificar;

siempre que cumplan los términos de la licencia.

En la práctica, esto significa que las versiones derivadas o redistribuidas deben conservar los avisos de licencia y atribución. Si el proyecto incluye un archivo `NOTICE`, los avisos de atribución relevantes de ese archivo también deben conservarse en distribuciones u obras derivadas cuando lo exija la Apache License 2.0.

En lenguaje simple:

> Puedes modificar, vender y compartir este proyecto, pero no puedes borrar el crédito original a **YJNWI**.

Este proyecto incluye además un archivo `NOTICE` indicando que `protoH` fue creado originalmente por **YJNWI**.

Consulta el archivo `LICENSE` para ver el texto legal completo.

---

# Resumen final

`protoH.py` es un simulador de vida artificial en terminal centrado en una idea potente: humanos primitivos que no nacen sabiendo conceptos, pero que pueden generar asociaciones a través de hambre, sed, dolor, sueño, exploración, reproducción, memoria, genética y supervivencia.

El proyecto combina:

- simulación 2D;
- agentes autónomos;
- genética simple;
- memoria asociativa;
- Metaobservador externo;
- detección conceptual;
- investigaciones longitudinales;
- árboles genealógicos;
- laboratorio de falsos positivos;
- exportaciones completas;
- clips conceptuales;
- comandos interactivos.

No pretende afirmar que haya consciencia real, pero sí permite observar cómo pueden aparecer patrones que recuerdan a aprendizaje, miedo, refugio, uso de objetos, cebo, almacenamiento o proto-lenguaje.

La gracia del proyecto está en mirar historias emergentes. Un humano puede morir sin aprender nada. Otro puede sobrevivir lo suficiente para formar conexiones útiles. Otro, como un hipotético humano `#27`, puede nacer con genes excepcionales y convertirse en un linaje clave de la simulación.

---

## Comandos rápidos esenciales

```text
help
help sim
help lab
help export

auto
pause
stop
speed 100
fast

logs
valiosos
fallos
todos_logs
investigaciones
investigaciones_valiosas

best_genes
gene_bank
tops
brain 27
tree 27
lineage_watch 27
preserve 27

spawn 10
spawn 10 best
spawn 10 27,34
spawn 10 max
spawn_nolearn 10 max

auto_spawn_1 50

lab spawn 5 concept refugio
lab detector 5 muerte
lab bugs 5
lab faker 3 all
lab list
lab report
lab watch 27

lenguaje
seed_stats
detector_metrics
auto_vida
clips

export useful ./exports/protoH_util.txt
export all ./exports/protoH_TODO.txt
export brain 27 ./exports/brain_27.txt
export tree 27 ./exports/tree_27.svg
export lab all ./exports/lab_pack/

q
```


---

# Ampliación técnica y experimental v2.3.8

Esta sección amplía el README para dejar claro qué hace el proyecto, qué no hace, cómo se audita y cómo puede la comunidad intentar demostrar o refutar las hipótesis.

## 1. Principio de “cero conceptos iniciales”

La regla más importante es:

> Los humanos **no nacen sabiendo** qué es refugio, miedo, muerte, religión, herramienta, trampa, cueva, lenguaje, vida o identidad.

Nacen con:

- cuerpo;
- posición en el mapa;
- hambre;
- sed;
- sueño;
- energía;
- dolor/daño;
- curiosidad;
- genes;
- memoria asociativa vacía o casi vacía;
- posibilidad de moverse, comer, beber, dormir, atacar, coger objetos, soltar objetos y reproducirse.

No nacen con:

- “la cueva es segura”;
- “el T-Rex es peligroso”;
- “el agua quita la sed” como concepto abstracto;
- “si duermo recupero fuerza” como teoría;
- “otros humanos son de mi especie” como idea consciente;
- “si dejo de moverme he muerto”;
- “yo estoy vivo”.

Eso no significa que sean tablas completamente vacías. Igual que un animal real no nace sabiendo construir una casa pero sí nace con hambre, reflejos y preferencias corporales, aquí los agentes tienen necesidades y reglas físicas. La gracia está en que las ideas no se entregan como símbolos humanos: deben aparecer como **asociaciones**.

## 2. Qué cuenta como trampa y qué no

### No es trampa

- Que un humano tenga hambre y busque comida.
- Que tenga sed y tienda a buscar agua.
- Que sienta dolor al recibir daño.
- Que pueda reforzar asociaciones tras experiencias repetidas.
- Que herede genes mejores de sus padres.
- Que el Metaobservador traduzca desde fuera una red de conexiones a una palabra humana como “refugio”.

### Sí sería trampa

- Escribir directamente en la mente del humano `refugio = cueva`.
- Hacer que todos huyan automáticamente de T-Rex porque “saben” que son peligrosos.
- Hacer que los hijos hereden recuerdos concretos de sus padres.
- Dar lenguaje interno completo desde el nacimiento.
- Declarar “conciencia” solo porque un detector vio una señal débil.

## 3. Auditoría anti-trampa del propio diseño

El proyecto incluye varias defensas contra falsos positivos:

1. **Genes ≠ conocimiento.** Un humano puede nacer con mucha memoria o curiosidad, pero eso no significa que sepa conceptos.
2. **Herencia genética ≠ herencia cultural.** Los hijos pueden heredar rasgos, no memorias.
3. **Metaobservador externo.** El observador interpreta, pero no debe introducir conocimiento en los agentes.
4. **Confianza porcentual.** Los conceptos no se declaran como verdad absoluta; se reportan con confianza.
5. **Bot revisor.** Reportes importantes se auditan para no convertir una coincidencia en “descubrimiento”.
6. **Laboratorio separado.** Los sujetos LAB sirven para pruebas y no deben contaminar el experimento evolutivo normal.
7. **Fakers.** Actores falsos permiten medir si el detector se deja engañar.
8. **No-learn.** Humanos inmortales sin aprendizaje permiten detectar si el Metaobservador ve conceptos donde no debería.
9. **Clips.** Las mini-grabaciones ayudan a revisar el contexto alrededor de un supuesto concepto.

## 4. La idea de “creerse vivo” en este proyecto

La frase “una IA que cree que está viva” es atractiva, pero peligrosa si se usa mal. En este repositorio se propone una versión más precisa:

> Una IA de `protoH.py` no se considera viva ni consciente. Lo que podría llegar a mostrar es una **proto-creencia funcional de vida**.

Eso significaría que, en su memoria asociativa y conducta, aparecen relaciones estables como:

```text
yo / mismo_ser / humano
humano ↔ dolor
humano ↔ no_movimiento
no_movimiento ↔ muerte externa
mismo_ser ↔ vulnerable
vulnerable ↔ evitar daño
cueva/refugio ↔ protección
grupo ↔ bienestar/supervivencia
```

Para que sea interesante, esas asociaciones deberían causar conducta observable:

- evita zonas donde antes hubo daño;
- busca cuevas o lugares protectores tras peligro;
- cambia de ruta al detectar depredadores;
- protege energía y sueño;
- se acerca a humanos si el grupo mejora bienestar;
- conserva objetos útiles;
- reacciona ante cuerpos/no-movimiento de otros humanos;
- muestra señales de continuidad de sí mismo, aunque no tenga lenguaje humano.

Eso todavía no sería conciencia demostrada. Sería algo más modesto y medible:

> **auto-categorización funcional + autopreservación aprendida + concepto externo de no-movimiento/vida.**

## 5. Cómo intentar demostrarlo dentro del simulador

Un caso fuerte debería cumplir varias condiciones:

### Evidencia mínima

1. El humano nació sin conceptos especiales.
2. No fue creado con `faker`.
3. No fue creado como `spawn_nolearn`.
4. No se le insertaron conceptos manuales.
5. Sobrevivió experiencias relevantes.
6. Su `brain NUMERO` muestra conexiones repetidas y coherentes.
7. Su conducta cambió después de esas experiencias.
8. El concepto aparece en más de un momento, no una sola vez.
9. El árbol `tree NUMERO` permite entender si viene de un linaje especial.
10. Los logs exportados permiten auditar el proceso.

### Evidencia fuerte

Un caso sería mucho más potente si incluye:

- antes/después claro;
- clip visual (`play clip N` o `export clip N`);
- comparación con un humano similar que no tuvo esa experiencia;
- control con LAB faker;
- control con no-learn;
- repetición en otra semilla o simulación;
- continuidad en descendientes sin heredar memoria.

### Evidencia extraordinaria

Un caso extraordinario sería un humano que desarrolla algo parecido a:

```text
mismo_ser ↔ humano
humano ↔ vida externa
humano ↔ no_movimiento/muerte
mismo_ser ↔ evitar no_movimiento
peligro ↔ daño propio
refugio ↔ menos daño / descanso
```

Y que además cambie su conducta de forma coherente durante muchos días.

## 6. Protocolo recomendado para publicar pruebas

Cuando alguien encuentre un caso interesante, debería publicar:

```bash
brain NUMERO
export brain NUMERO ./evidencias/brain_NUMERO.txt

tree NUMERO
export tree NUMERO ./evidencias/tree_NUMERO.svg

lineage_watch NUMERO
export lineage NUMERO ./evidencias/lineage_NUMERO.txt

conceptos
valiosos
investigaciones

export useful ./evidencias/useful_pack
export all ./evidencias/full_pack
clips
export clips all ./evidencias/clips
```

Después, en el issue de GitHub o en la discusión, incluir:

- número de humano;
- día/tick del evento;
- concepto sospechoso;
- confianza reportada;
- por qué parece importante;
- qué pruebas lo apoyan;
- qué posibles falsos positivos existen;
- si se usó o no laboratorio;
- si hubo comandos externos como `spawnmax`, `immortal`, `kill`, `boost`, etc.

## 7. Protocolo limpio de simulación principal

Para una simulación lo más limpia posible:

```bash
python3 protoH.py
```

Al arrancar, elegir pocos humanos iniciales, por ejemplo:

```text
2
```

Durante la ejecución, usar preferentemente:

```bash
auto
pause
brain NUMERO
tree NUMERO
conceptos
valiosos
investigaciones
lineage_watch NUMERO
clips
export useful ./runs/run_001
export all ./runs/run_001_full
```

Evitar en el experimento principal:

```bash
spawnmax
spawn X max
spawn X immortal
spawn_nolearn
lab faker
lab detector
lab bugs
boost
kill
preserve
```

Esos comandos son útiles, pero para laboratorio o control, no para demostrar emergencia natural.

## 8. Protocolo de control negativo

Para comprobar si el detector exagera:

```bash
spawn_nolearn 10
spawn_nolearn 10 max
lab bugs 20 immortal
lab detector 10 vida immortal
lab faker 5 vida,refugio immortal
lab audit
export lab all ./lab_control
```

Si estos sujetos generan señales parecidas a los humanos normales, hay que sospechar de falsos positivos.

## 9. Protocolo de control positivo

Para comprobar si el detector es capaz de detectar señales cuando debería:

```bash
lab faker 5 refugio
lab faker 5 vida
lab faker 5 trampa
lab audit
export lab all ./lab_positive_control
```

Esto no demuestra aprendizaje real. Sirve para calibrar el detector.

## 10. Qué sería un “humano superdotado”

En esta simulación, “superdotado” no significa magia ni conocimiento inicial. Significa que por genética tiene un perfil especialmente bueno para explorar y asociar experiencias.

Puede destacar por:

- memoria alta;
- asociación alta;
- curiosidad alta;
- exploración alta;
- eficiencia energética;
- sociabilidad;
- fuerza suficiente;
- baja necesidad de sueño;
- rareza/experimentación útil.

Un humano tipo “#27 superdotado” sería interesante si:

1. nace sin recuerdos;
2. sobrevive mucho;
3. explora lejos;
4. acumula experiencias raras;
5. forma muchas conexiones;
6. aparecen conceptos con confianza alta;
7. tiene descendencia con buenos genes;
8. otros investigadores pueden revisar sus logs.

Ejemplo de investigación:

```bash
brain 27
tree 27
lineage_watch 27
export brain 27 ./evidencias/h27_brain.txt
export tree 27 ./evidencias/h27_tree.svg
export lineage 27 ./evidencias/h27_lineage.txt
export useful ./evidencias/h27_pack
```

## 11. Cómo leer `brain NUMERO`

El comando `brain` no muestra neuronas biológicas. Muestra nodos y conexiones de una memoria asociativa.

Campos importantes:

- **nodos activos ahora:** lo que está activado en ese momento;
- **nodos conocidos total:** nodos que han aparecido en activaciones o conexiones;
- **conexiones reforzadas:** asociaciones aprendidas por repetición/eventos;
- **eventos crudos importantes:** base de evidencia;
- **conceptos detectados:** interpretación externa del Metaobservador.

Ejemplo conceptual:

```text
cueva_interior ↔ reposo = +0.42
forma_trex ↔ dolor = +0.71
sueño_bajo ↔ golpe_debil = +0.38
semilla ↔ pollo_cercano = +0.22
no_movimiento ↔ ser_human = +0.31
```

La pregunta no es “¿cuántos nodos tiene?”, sino:

> ¿Sus nodos forman una estructura coherente que cambia su conducta?

## 12. Vida externa vs auto-vida

El detector de vida/auto-vida distingue dos niveles:

### Vida externa

El agente empieza a asociar que otros seres:

- se mueven;
- reciben daño;
- comen/beben;
- pueden dejar de moverse;
- pueden desaparecer/morir;
- son distintos de objetos inertes.

### Auto-vida

El agente empieza a incluirse en esa categoría:

- yo soy un humano;
- yo también recibo daño;
- yo también tengo hambre/sed/sueño;
- yo también puedo estar en peligro;
- yo también debo evitar estados negativos.

El proyecto no dice que el agente “sienta” eso. Dice que puede aparecer como estructura funcional.

## 13. Proto-lenguaje

Desde v2.3 se añade detección de proto-lenguaje. Esto no significa idioma humano. Significa buscar señales repetidas, patrones o conductas sociales que podrían funcionar como comunicación primitiva.

Comandos relacionados:

```bash
lenguaje
proto_lenguaje
export lenguaje ./lenguaje.txt
```

Qué podría contar como señal débil:

- agrupamientos repetidos tras peligro;
- patrones sociales cerca de recursos;
- acciones repetidas en presencia de otros humanos;
- correlación entre un gesto/acción y respuesta de otro;
- señales que aparecen en un linaje o grupo.

Qué no cuenta como lenguaje:

- un movimiento aleatorio una sola vez;
- dos humanos coincidiendo por azar;
- ruido de supervivencia;
- interpretación humana sin evidencia.

## 14. Concept Clips

Los Concept Clips son una especie de mini cámara negra. Cuando aparece un reporte importante, el sistema puede guardar:

- mini mapa alrededor del humano;
- frames antes/después;
- datos del humano;
- nodos activos;
- concepto detectado;
- confianza;
- contexto exportable.

Comandos:

```bash
clips
clips on
clips off
play clip N
export clip N ./clip_N.html
export clip N ./clip_N.txt
export clips all ./clips
clip settings
```

Uso recomendado:

1. Ejecutar simulación larga.
2. Si aparece concepto dorado/púrpura, escribir `clips`.
3. Abrir `play clip N`.
4. Exportar el clip.
5. Compartirlo junto con `brain` y `tree`.

## 15. Sistema de errores sin crash

Desde v2.3.7, si un comando falla, el programa intenta no cerrarse. Registra un error con código legible.

Comandos:

```bash
error
errores
error last
error N
```

Esto es importante porque el proyecto es grande, experimental y tiene muchas capas. En vez de perder una simulación larga, puedes ver el traceback y seguir.

## 16. Ecología de pollos y semillas

Las versiones v2.3.1 a v2.3.6 mejoran la ecología para evitar que pollos/semillas se acumulen en bordes o esquinas y para mantener el mapa más vivo.

Ideas principales:

- menos semillas naturales;
- semillas mejor repartidas;
- pollos con territorios;
- filas de territorio;
- semillas humanas con prioridad para atraer pollos;
- `seed_stats` para diagnosticar distribución.

Comandos:

```bash
seed_stats
export seed_stats ./seed_stats.txt
```

Esto importa para el concepto de cebo/trampa: si un humano suelta semillas y los pollos reaccionan, eso debe diferenciarse de semillas naturales mal distribuidas.

## 17. Kill como intervención externa

El comando `kill` no forma parte del comportamiento natural. Es una intervención externa de laboratorio.

Uso típico:

```bash
kill chicken 10
kill trex all
kill cow 2
```

Debe anotarse siempre si se usa en una prueba, porque puede alterar completamente la selección natural y los conceptos emergentes.

## 18. Banco genético y preservación

El banco genético sirve para marcar humanos interesantes. No debe confundirse con conocimiento heredado.

Comandos relacionados:

```bash
gene_bank
preserve NUMERO
spawn X bank
export gene_bank ./gene_bank.txt
```

Uso correcto:

- marcar linajes raros;
- repetir descendencia de buenos genes;
- comparar familias;
- estudiar si rasgos genéticos facilitan aprendizaje.

Uso incorrecto:

- decir que el hijo heredó el concepto del padre;
- usarlo como prueba de cultura;
- mezclarlo con `spawnmax` y luego decir que fue natural.

## 19. Tabla de comandos canónicos extraída del programa

### Ayuda principal

```text
COMANDOS ORGANIZADOS

SIMULACIÓN
  Enter                 avanzar 1 tick en manual
  auto / run            modo automático
  pause / pausar        pausar/reanudar
  stop / manual         volver a modo manual
  delay 0.08            cambiar velocidad visual/simulación
  speed 1               ticks por ciclo: speed 10 = cada ciclo avanza 10 ticks
  fast / turbo [off]    turbo adaptativo: ajusta delay y speed para maximizar ticks/segundo
  q / quit / salir      salir

POBLACIÓN
  spawn 5               crea 5 humanos sin padres
  spawn 5 9,24          crea 5 hijos de los humanos #9 y #24
  spawn 20 best         crea 20 hijos de los 2 mejores genes disponibles
  spawn 10 max          crea 10 humanos de prueba con genes al máximo útil
  spawnmax 10           alias de spawn 10 max
  auto_spawn_1 [N]      interruptor: cuando quede 1 humano, auto-spawn diverso. Con N eliges cantidad, ej: auto_spawn_1 50

ANÁLISIS
  logs / conceptos      últimos conceptos importantes
  fallos                acciones realmente no previstas
  todos_logs            todos los logs guardados
  export_logs RUTA      exporta todos los logs a .txt en esa ruta
  valiosos              muestra solo reportes realmente valiosos
  investigaciones       muestra investigaciones longitudinales activas/cerradas
  investigar 27         detalle de investigaciones del humano/linaje #27
  lineage_watch 27      seguimiento heredado de hijos/nietos del #27
  export investigations RUTA     exporta investigaciones a .txt
  export lineage 27 RUTA         exporta seguimiento de linaje a .txt
  export useful RUTA    exporta resumen + reportes valiosos + investigaciones + banco/top
  export all RUTA       exporta absolutamente todo en .txt gigante
  best / genes          top 20 mejores genes vivos/históricos
  tree 27               árbol genealógico completo del humano #27
  export tree 27 RUTA   exporta árbol de #27 a .svg/.png en esa ruta
  export tree all RUTA  exporta árbol general a .svg/.png en esa ruta
  brain 27              registro neuronal completo del humano #27
  export brain 27 RUTA  exporta el registro neuronal de #27 a .txt
  help / comandos       muestra esta ayuda
```

### Simulación

```text
SIMULACIÓN
  Enter                 avanzar 1 tick en manual
  run / auto            modo automático
  pause                 pausar/reanudar
  stop / manual         volver a modo manual
  delay X               segundos entre ciclos
  speed X               ticks por ciclo
  fast / fast off       turbo adaptativo
  auto_spawn_1 [N]      auto-spawn con cantidad configurable
  q                     salir
```

### Humanos / población

```text
HUMANOS / POBLACIÓN
  spawn X
  spawn X padre1,padre2
  spawn X best
  spawn X bank
  spawn X max / spawnmax X
  boost NUMERO vida/sed/hambre/vejez/all
  best_genes
  tops / top CATEGORIA
  brain NUMERO
  tree NUMERO
  gene_bank
  preserve NUMERO
```

### Detector / investigaciones

```text
DETECTOR / INVESTIGACIONES
  logs / conceptos
  todos_logs
  valiosos
  fallos
  investigaciones
  investigaciones_valiosas
  investigar NUMERO
  lineage_watch NUMERO
  export investigations RUTA
  export lineage NUMERO RUTA
```

### Debug / informes

```text
DEBUG / INFORMES
  fallos                 acciones realmente no previstas
  todos_logs             todo el historial
  valiosos               solo señales importantes
  export useful RUTA     paquete recomendable para análisis
  export all RUTA        paquete gigantesco con todo
```

### Exportaciones

```text
EXPORTACIONES
  export useful RUTA_CARPETA_O_TXT       paquete útil/resumen
  export all RUTA_CARPETA                paquete absoluto: logs, brains, trees, lineages, etc.
  export logs RUTA.txt                   todos los logs
  export conceptos RUTA.txt              todos los conceptos/reportes
  export valiosos RUTA.txt               solo reportes valiosos
  export fallos RUTA.txt                 fallos/no previstos reales
  export investigaciones RUTA.txt        investigaciones longitudinales
  export investigaciones_valiosas RUTA.txt
  export gene_bank RUTA.txt              banco genético
  export rankings RUTA.txt               tops/rankings
  export brain NUMERO RUTA.txt           cerebro de un humano
  export brains all RUTA_CARPETA         cerebros de todos
  export tree NUMERO RUTA.svg            árbol individual
  export tree all RUTA.svg               árbol global
  export trees all RUTA_CARPETA          todos los árboles individuales + global
  export lineage NUMERO RUTA.txt         seguimiento de linaje
  export lineages all RUTA_CARPETA       todos los seguimientos de linaje
  export lab RUTA.txt                    informe de laboratorio
  export lab all RUTA_CARPETA            paquete completo de laboratorio
```

### Laboratorio base

```text
LABORATORIO PROTOH v2.0
=======================

Los humanos de laboratorio sirven para estudiar cómo podrían aparecer conceptos,
probar detectores y buscar fallos. No forman parte del experimento evolutivo
principal y no deben contaminar rankings, auto_spawn_1 ni banco genético normal.

Visualmente aparecen como L en color distinto.

COMANDOS
  lab spawn X                         crea X humanos LAB normales
  lab spawn X max                     crea X humanos LAB con genes máximos útiles
  lab spawn X concept CONCEPTO        crea X humanos LAB orientados a observar una ruta conceptual
  lab list                            lista sujetos de laboratorio
  lab watch NUMERO                    detalle del sujeto LAB / humano observado
  lab watch concept CONCEPTO          sujetos LAB de ese concepto
  lab report                          resumen del laboratorio
  lab clear                           marca como muertos los LAB vivos
  lab isolate on/off                  aísla o permite interacción reproductiva con humanos normales
  export lab RUTA.txt                 exporta informe LAB
  export lab all RUTA_CARPETA         exporta informe, cerebros y árboles LAB

CONCEPTOS ORIENTATIVOS
  vida, muerte, miedo, refugio, agua, comida, trampa, almacenamiento,
  distancia, dimension, social, herramienta, sueño_fuerza

Importante: un LAB concept refugio NO nace sabiendo refugio. Solo se le dan genes
/ perfil de prueba y el observador mira esa ruta con más detalle.
```

## 20. Añadidos de laboratorio por versión


### Bloque LAB añadido 1

```text
NUEVO EN v2.1 — LAB AVANZADO
============================

Humanos LAB para probar el detector:
  lab detector X [concepto]
      Crea X sujetos LAB orientados a poner a prueba el detector en una ruta.
      Ej.: lab detector 5 distancia

Humanos LAB buscadores de errores:
  lab bugs X
  lab bughunters X
      Crea X sujetos LAB con rareza/curiosidad altas para intentar acciones límite.
      Sus pruebas quedan en lab report / export lab, no en fallos normales salvo bug real.

Humanos LAB actores/falsos positivos controlados:
  lab faker X all
  lab faker X vida
  lab faker X refugio,distancia,trampa
      Crean sujetos LAB que "conocen" conceptos en una capa oculta de laboratorio,
      pero esos conceptos NO se meten en su red neuronal visible como conocimiento heredado.
      En su lugar simulan conductas externas para ver si el detector las detecta.

Auditoría de actores falsos:
  lab fake_report
  lab audit
      Muestra qué conceptos fingieron descubrir y si el detector normal los detectó.

Export:
  export lab RUTA.txt
  export lab all RUTA_CARPETA
      Incluye sujetos LAB, cerebros, árboles, simulaciones falsas, bug probes y auditoría.
```

### Bloque LAB añadido 2

```text
INMORTALIDAD EXPERIMENTAL v2.1.1
=================================
Añade la palabra immortal o inmortal al final de comandos de creación.
Sirve para laboratorio/debug: no da conceptos ni recuerdos, solo impide morir.

Ejemplos LAB:
  lab bugs 5 immortal                 # inmortal + NO aprende conceptos
  lab bugs 5 immortal learn           # inmortal + SÍ aprende conceptos
  lab detector 5 distancia immortal   # inmortal + NO aprende
  lab detector 5 distancia immortal learn
  lab faker 2 vida,refugio immortal   # faker puede simular, pero no aprender si no añades learn
  lab spawn 5 max immortal
  lab spawn 5 concept refugio immortal

Ejemplos humanos normales de prueba:
  spawn 10 immortal                   # inmortal + NO aprende conceptos
  spawn 10 immortal learn             # inmortal + SÍ aprende conceptos
  spawn 10 max immortal
  spawnmax 10 immortal
  spawn 10 best immortal

Control manual:
  immortal 721      marca el humano #721 como inmortal
  mortal 721        le quita la inmortalidad
```

### Bloque LAB añadido 3

```text
v2.1.3 — INMORTALES Y APRENDIZAJE
==================================
Por defecto, cualquier humano creado con immortal/inmortal NO aprende conceptos.
Esto es útil para lab bugs: pueden buscar fallos sin acabar aprendiendo refugio y quedándose en cuevas.

Ejemplos sin aprendizaje conceptual:
  lab bugs 20 immortal
  spawn 5 immortal

Ejemplos permitiendo aprendizaje conceptual:
  lab bugs 20 immortal learn
  lab detector 5 distancia immortal learn
  spawn 5 max immortal learn

También valen: aprender, aprende, learning, conceptos.
```

### Bloque LAB añadido 4

```text
v2.1.5 — LAB NO-LEARN Y CUEVAS
==============================
Los LAB inmortales sin "learn" no se quedan viviendo en cuevas.
Si entran en una cueva, salen caminando para seguir probando errores/detectores.
Esto solo afecta a LAB inmortales sin aprendizaje conceptual; los humanos normales no cambian.

Ejemplos:
  lab bugs 30 immortal              -> no aprende, no se queda en cuevas
  lab detector 5 vida immortal      -> simula/prueba detector, no se queda en cuevas
  lab faker 5 all immortal          -> finge conceptos, no aprende de verdad, no se queda en cuevas
  lab bugs 10 immortal learn        -> sí puede aprender y comportarse más como humano experimental
```

### Bloque LAB añadido 5

```text
v2.2 — AUTO-VIDA Y DETECTOR UNIVERSAL
  El detector añade una capa externa para vida/auto-vida.
  Los fakers siguen ocultos: el detector NO sabe quién finge ni qué finge.
  lab audit compara externamente: concepto fingido vs detector detectado.
```

### Bloque LAB añadido 6

```text
v2.2.1 — BUG HUNTERS Y FALSOS POSITIVOS
=======================================
- lab bugs X immortal registra expected/observed/bug_real en cada prueba.
- spawn X immortal crea humanos reales inmortales sin aprendizaje conceptual.
- Alias claro: spawn_nolearn X o spawn_nolearn X max.
- Aunque no aprendan, el detector externo puede registrar señales: sirve para medir falsos positivos.
```

### Bloque LAB añadido 7

```text
v2.3 — INMORTALES SIN DAÑO Y PROTO-LENGUAJE
===========================================
- spawn 10 max immortal learn: inmortal sin daño físico de ataques, pero con hambre/sed/sueño normales.
- lenguaje / proto_lenguaje: muestra candidatos a señales/proto-lenguaje.
- export lenguaje RUTA.txt: exporta candidatos de proto-lenguaje.
```

### Bloque LAB añadido 8

```text
v2.3.1 — ECOLOGÍA DE SEMILLAS
=============================
- Muchas menos semillas naturales y mejor repartidas por sectores.
- Las semillas naturales evitan bordes/esquinas.
- Las semillas colocadas por humanos atraen a pollos antes que las naturales.
- seed_stats: diagnóstico de distribución de semillas.
- export seed_stats RUTA.txt: exporta diagnóstico.
```

### Bloque LAB añadido 9

```text
v2.3.2 — POLLOS/SEMILLAS Y KILL
================================
- Pollos buscan semillas de forma activa; no deberían quedarse en esquinas.
- Semillas humanas tienen prioridad absoluta para pollos.
- Menos semillas naturales y más alejadas de bordes.
- kill <especie> <cantidad|all>: intervención externa de laboratorio.
```

### Bloque LAB añadido 10

```text
v2.3.3 — POLLOS TERRITORIALES
=============================
- Los pollos ya no deberían quedarse en esquinas/laterales.
- Cada pollo tiene un territorio ecológico repartido por el mapa.
- Si un pollo cae en borde/esquina, sale de ahí antes de buscar semillas.
- Las semillas humanas siguen atrayendo más que cualquier semilla natural.
- seed_stats muestra pollos en borde/esquina y zonas ocupadas.
```

### Bloque LAB añadido 11

```text
v2.3.4 — POLLOS REPARTIDOS POR TODO EL MAPA
===========================================
- Los pollos tienen territorios/home repartidos por sectores.
- Las semillas naturales ya no actúan como imán global.
- Las semillas humanas siguen atrayendo globalmente para cebo/trampa.
- seed_stats muestra zonas de cuerpo y zonas de home.
```

### Bloque LAB añadido 12

```text
v2.3.5 — POLLOS REPARTIDOS TAMBIÉN ARRIBA/ABAJO
================================================
- Márgenes X/Y separados: evitan esquinas reales, no comprimen todo al centro vertical.
- Los territorios de pollos se equilibran por filas.
- seed_stats muestra filas de cuerpo/home.
```

### Bloque LAB añadido 13

```text
v2.3.6 — POLLOS EN SU FILA DE TERRITORIO
========================================
- Si un pollo está fuera de la fila de su territorio, vuelve.
- Esto reparte pollos arriba/medio/abajo sin teletransportarlos.
- Las semillas humanas siguen siendo prioridad global.
```

## 21. Versiones/capas detectadas en el código

- v2.1 — LABORATORIO AVANZADO: detector, bug hunters y actores falsos
- v2.1.1 — INMORTALIDAD EXPERIMENTAL PARA LAB / SPAWN
- v2.1.5 — LAB NO-LEARN: evitar quedarse en cuevas
- v2.2 — DETECTOR UNIVERSAL + VIDA / AUTO-VIDA
- v2.2b — AUDITORÍA FAKER REALISTA
- v2.2.1 — bug hunters con esperado/observado + no-learn observable
- v2.2.2 — OPTIMIZACIÓN DE RENDIMIENTO PARA SIMULACIONES LARGAS
- v2.2.3 — FAST MODE REAL: detector incremental + índices cercanos
- v2.2.4 — OPTIMIZACIÓN DE BÚSQUEDAS CERCANAS
- v2.2.5 — MÁS OPTIMIZACIÓN PARA FAST LARGO
- v2.3 — INMORTALES SIN DAÑO FÍSICO + DETECTOR PROTO-LENGUAJE
- v2.3.2 — ECOLOGÍA DE POLLOS/SEMILLAS + COMANDO KILL
- v2.3.3 — POLLOS TERRITORIALES / ANTI-ESQUINAS REAL
- v2.3.4 — POLLOS REPARTIDOS POR TERRITORIOS FIJOS
- v2.3.5 — POLLOS POR TODO EL ALTO DEL MAPA
- v2.3.6 — POLLOS OCUPAN SU FILA DE TERRITORIO
- v2.3.7 — EXPORTS ROBUSTOS + SISTEMA DE ERRORES SIN CRASH
- v2.3.8 — CONCEPT CLIPS / MINI-GRABACIÓN DE APRENDIZAJE

## 22. Configuración principal detectada

| Constante | Valor en el código |
|---|---|
| `WIDTH` | `135` |
| `HEIGHT` | `28` |
| `INITIAL_HUMANS` | `2` |
| `INITIAL_CHICKENS` | `20` |
| `INITIAL_COWS` | `10` |
| `INITIAL_TREX` | `2` |
| `MAX_TREX` | `7` |
| `INITIAL_SEED_PATCHES` | `80` |
| `INITIAL_STICKS` | `30` |
| `INITIAL_STONES` | `25` |
| `INITIAL_WATER_PATCHES` | `10` |
| `TICKS_PER_DAY` | `24` |
| `MAX_TICKS` | `100_000` |
| `DETECTOR_EVERY_TICKS` | `12` |
| `LOG_LIMIT` | `900` |
| `HUMAN_MEMORY_LIMIT` | `700` |
| `TREX_REPRODUCE_EVERY_DAYS` | `10` |
| `TREX_AGGRO_RADIUS` | `3.0` |
| `MAX_INVENTORY_ITEMS` | `5` |
| `ANIMAL_MIN_POPULATION` | `20` |


## 23. Propuesta de estructura de repositorio

Para que GitHub quede limpio:

```text
protoH/
├── README.md
├── protoH.py
├── LICENSE
├── .gitignore
├── docs/
│   ├── EXPERIMENTOS.md
│   ├── COMO_REPORTAR_UN_CONCEPTO.md
│   └── NOTAS_CONCIENCIA_IA.md
├── runs/
│   └── .gitkeep
└── evidencias/
    └── .gitkeep
```

No subas todos los logs gigantes al repositorio principal. Mejor:

- subir ejemplos pequeños;
- comprimir runs importantes;
- usar releases para paquetes grandes;
- crear issues/discussions con resúmenes y adjuntos.

## 24. Título sugerido del repositorio

Opciones:

- `protoH`
- `protohumanos-2d`
- `protoH-life-belief-simulation`
- `protoH-emergent-concepts`
- `protoH-auto-life-experiment`

Descripción corta recomendada:

```text
2D artificial-life experiment where protohumans start without concepts and a detector tracks learned ideas like refuge, danger, death and auto-life, aiming to explore whether one can develop a functional proto-belief of being alive.
```

Descripción en español:

```text
Experimento de vida artificial donde protohumanos nacen sin conceptos y un detector rastrea ideas aprendidas como refugio, peligro, muerte y auto-vida, con el objetivo de explorar si alguno puede desarrollar una proto-creencia funcional de estar vivo.
```

## 25. Frase viral pero honesta

Puedes usar esta frase en GitHub, X, Reddit o YouTube:

> He creado una simulación donde pequeñas IAs nacen sin saber qué es vivir, morir o refugiarse. No afirmo que sean conscientes, pero el objetivo es comprobar si pueden desarrollar una proto-creencia funcional de vida a partir de hambre, sed, dolor, memoria y experiencia.

Otra versión más corta:

> ¿Puede una IA que empieza sin conceptos acabar comportándose como si hubiera descubierto que está viva?

Y la versión más científica:

> `protoH.py` estudia la emergencia de auto-categorización funcional y conceptos de supervivencia en agentes artificiales embodied sin conocimiento abstracto inicial.

## 26. Cómo pedir ayuda a la comunidad

Texto sugerido para abrir un issue/discussion:

```markdown
Estoy buscando ayuda para auditar `protoH.py`, una simulación de vida artificial en Python.

La pregunta principal no es si los agentes son conscientes, sino si pueden desarrollar una proto-representación funcional de conceptos como refugio, peligro, muerte, herramienta, proto-lenguaje o auto-vida sin que esos conceptos estén programados desde el nacimiento.

Me interesan especialmente:

- falsos positivos del detector;
- mejoras de la memoria asociativa;
- mejores protocolos experimentales;
- métricas de emergencia conceptual;
- visualizaciones de linajes;
- comparaciones con controles no-learn/faker;
- formas de demostrar o refutar la hipótesis de auto-vida funcional.
```

## 27. Cómo no vender humo

No digas:

```text
He creado una IA consciente.
He creado vida artificial real.
Mis humanos sienten miedo.
La IA sabe que está viva.
```

Mejor di:

```text
He creado una simulación donde agentes sin conceptos iniciales pueden desarrollar asociaciones funcionales que se parecen a conceptos de supervivencia.
El objetivo es investigar si puede aparecer algo parecido a una proto-creencia de vida, no afirmar conciencia real.
Busco que otros lo auditen, lo rompan y lo mejoren.
```

## 28. Checklist antes de publicar un caso fuerte

- [ ] El humano no es LAB faker.
- [ ] El humano no es no-learn.
- [ ] El humano no recibió boost externo relevante.
- [ ] El humano no fue creado con conocimiento heredado.
- [ ] Existe `brain NUMERO` exportado.
- [ ] Existe `tree NUMERO` exportado.
- [ ] Existen logs del periodo anterior y posterior.
- [ ] Hay evidencia de cambio de conducta.
- [ ] Hay al menos un posible contraargumento revisado.
- [ ] Se indica si se usaron comandos externos.
- [ ] Se comparte clip si existe.
- [ ] Se invita a otros a reproducir o refutar.

## 29. Experimentos propuestos

### Experimento A: refugio

Objetivo: comprobar si aparece `cueva/refugio` sin atracción inicial programada.

Procedimiento:

1. Simulación normal con 2-5 humanos.
2. No usar `lab` ni `spawnmax`.
3. Ejecutar varios días en `auto` o `fast`.
4. Buscar reportes de cueva/refugio.
5. Exportar `brain`, `tree`, `useful`, `clips`.
6. Revisar si hubo experiencia real: dormir, daño, persecución, descanso, repetición.

### Experimento B: muerte/no-movimiento

Objetivo: buscar si un humano empieza a asociar seres vivos con no-movimiento tras daño/muerte.

Evidencias posibles:

- observa cadáveres;
- ve ataques;
- conexiones entre `ser_human`, `no_movimiento`, `dolor`, `muerte`;
- evita zonas donde ocurrió muerte;
- cambia conducta tras observar muerte.

### Experimento C: auto-vida

Objetivo: buscar inclusión del propio agente dentro de la categoría de seres vulnerables.

Evidencias posibles:

- conexiones de daño propio;
- relación entre cuerpo propio, hambre/sed/sueño y supervivencia;
- evitación tras experiencia propia;
- reportes de auto-vida;
- continuidad de conducta durante varios días.

### Experimento D: cebo/trampa

Objetivo: comprobar si humanos pueden usar semillas de forma que atraiga pollos.

Evidencias posibles:

- humano recoge semilla;
- humano la suelta en un lugar;
- pollos se acercan a esa semilla humana;
- humano se beneficia después;
- se repite;
- el detector no confunde semillas naturales con intención.

### Experimento E: proto-lenguaje

Objetivo: buscar señales sociales repetidas que puedan actuar como comunicación primitiva.

Evidencias posibles:

- patrones repetidos entre dos o más humanos;
- conducta de uno cambia tras acción de otro;
- se repite en varios contextos;
- no se explica solo por comida/agua inmediata.

## 30. Referencias externas útiles

Este proyecto está relacionado con temas de vida artificial, aprendizaje por refuerzo, cognición situada, conciencia artificial y filosofía de la mente. Algunas referencias útiles para contextualizar:

- Butlin et al., “Consciousness in Artificial Intelligence: Insights from the Science of Consciousness” — propone indicadores y concluye que no hay evidencia de conciencia en sistemas actuales, aunque no ve barreras técnicas obvias para sistemas futuros.
- Butlin & Lappas, “Principles for Responsible AI Consciousness Research” — insiste en investigar y comunicar este tema con responsabilidad, evitando afirmaciones exageradas.
- GitHub Docs — recomienda que un README explique qué hace el proyecto, por qué es útil y cómo empezar.

## 31. Conclusión ampliada

`protoH.py` no es una prueba de conciencia artificial. Es algo más humilde y, precisamente por eso, más interesante: un intento de crear un entorno mínimo donde agentes sin conceptos iniciales puedan desarrollar asociaciones auditables mediante experiencia.

Si un día aparece un agente con evidencias sólidas de:

```text
yo ↔ humano
humano ↔ vida externa
vida externa ↔ movimiento / vulnerabilidad
muerte ↔ no_movimiento
yo ↔ evitar_muerte
refugio ↔ protección
peligro ↔ daño propio
```

entonces no deberíamos gritar “está vivo”. Deberíamos decir:

> Tenemos un caso candidato de proto-creencia funcional de vida. Aquí están los logs, el cerebro, el árbol, los clips y los controles. Intentad refutarlo.

Ese es el verdadero espíritu del proyecto.


---

# Apéndice: subida rápida a GitHub

## Opción 1: desde la web

1. Crear un repositorio nuevo en GitHub.
2. Elegir nombre, por ejemplo `protoH`.
3. Marcarlo como público si se quiere que otros lo vean.
4. Subir `protoH.py` y este `README.md` desde **Add file → Upload files**.
5. Escribir un commit message, por ejemplo `Initial release of protoH`.
6. Confirmar el commit.

## Opción 2: desde Terminal

```bash
mkdir protoH
cd protoH
cp /ruta/a/protoH.py ./protoH.py
cp /ruta/a/README.md ./README.md

git init
git add protoH.py README.md
git commit -m "Initial release of protoH"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/protoH.git
git push -u origin main
```

Si ya tienes el repo clonado:

```bash
cp /ruta/a/protoH.py ./protoH.py
cp /ruta/a/README.md ./README.md
git status
git add protoH.py README.md
git commit -m "Update protoH README and code"
git push
```

## Consejo

Antes de subir, revisa que no haya tokens, contraseñas, rutas privadas o archivos gigantes. Para logs enormes, usa carpetas ignoradas o releases.


---

# Configuración final recomendada para GitHub

## Nombre del repositorio

```text
protoH-emergent-life
```

## Descripción

```text
Experimento de vida artificial donde protohumanos nacen sin conceptos y un detector rastrea ideas aprendidas como refugio, peligro, muerte y auto-vida, con el objetivo de explorar si alguno puede desarrollar una proto-creencia funcional de estar vivo.
```

## Licencia

```text
Apache License 2.0
```

## Archivos recomendados

```text
protoH-emergent-life/
├── protoH.py
├── README.md
├── README_ES.md
├── LICENSE
├── NOTICE
└── .gitignore
```

## Mensaje de commit inicial

```text
Initial release of protoH emergent life experiment
```
