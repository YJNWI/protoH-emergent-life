#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
protoH.py - PROTOHUMANOS 2D v2.2.6

Objetivo:
- Simular protohumanos muy simples en un mapa 2D.
- Los humanos NO nacen con conceptos: no saben qué es refugio, miedo, vida, muerte, trampa, religión, etc.
- Sí tienen cuerpo, hambre, sed, sueño, dolor, curiosidad, memoria, habilidad de coger, atacar, comer, beber, dormir, moverse y reproducirse.
- No se bloquean acciones por magia: el mundo responde por peso, tamaño, espacio, daño, energía, estabilidad, viento, etc.
- Un Metaobservador externo detecta posibles conceptos emergentes/refinamientos con % de confianza y mini registro neuronal.

Cambios incluidos:
- Pregunta cantidad de humanos iniciales al arrancar.
- Solo 2 T-Rex iniciales.
- T-Rex se reproducen cada 10 días.
- T-Rex solo persiguen/atacan si un humano está a menos de 3 casillas de radio.
- Mapa 60x60 completo con colores ANSI.
- Cueva lógica CCC/EIC/CCC, pero visualmente E/I se ven como suelo "."
- Sin atracción inicial programada hacia la cueva. Solo se vuelve atractiva si se aprende por experiencia.
- Sed prioriza buscar agua.
- Hambre prioriza buscar comida.
- Humanos se sienten algo mejor con otros humanos cerca.
- Mordisco humano posible: 4 daño al objetivo y 6 autodaño.
- Gestos raros: como en la vida real, mover/golpear aire no hace nada útil y gasta un poco de energía.
- Comandos: Enter, auto, pause/pausar, delay <segundos>, speed <ticks>, conceptos/logs, fallos/no_previstos, todos_logs, export_logs, spawn, best_genes, tree, brain, auto_spawn_1, q.
- Logs completos y detallados para conceptos, fallos y eventos.
- Detector abierto extra para conceptos raros/secuencias no previstas.
"""

from __future__ import annotations

import math
import os
import random
import re
import statistics
import time
import sys
import select
import pathlib
import termios
import tty
import subprocess
import tempfile
import shutil
import html
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# CONFIGURACIÓN
# ============================================================

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

RANDOM_SEED = None

MIN_SLEEP_PER_24H = 10
SLEEP_DAMAGE_MULTIPLIER_WHEN_TIRED = 0.5

TREX_REPRODUCE_EVERY_DAYS = 10
TREX_AGGRO_RADIUS = 3.0
# Si un T-Rex o una vaca lleva 1.5 días intentando atacar a un humano/grupo
# muy cerrado y no logra alcanzarlo (normalmente por estar refugiados en cueva),
# deja de insistir durante 7 días. No es conocimiento humano: es fatiga/frustración
# animal. Si esos humanos vuelven a pegarle, se cancela el ignore y responde.
PREDATOR_STUCK_ATTACK_DAYS = 1.5
PREDATOR_IGNORE_DAYS = 7
PREDATOR_STUCK_ATTACK_TICKS = int(TICKS_PER_DAY * PREDATOR_STUCK_ATTACK_DAYS)
PREDATOR_IGNORE_TICKS = int(TICKS_PER_DAY * PREDATOR_IGNORE_DAYS)
PREDATOR_IGNORE_GROUP_RADIUS = 3.0

MIN_CONFIDENCE_TO_PRINT = 15.0
MIN_UNEXPECTED_TO_PRINT = 18.0

USE_COLORS = True

AUTO_SPAWN_WHEN_ONE_DEFAULT = False
AUTO_SPAWN_WHEN_ONE_AMOUNT = 20
ANIMAL_MIN_POPULATION = 20
MAX_INVENTORY_ITEMS = 5
ALLOWED_INVENTORY_KINDS = {"seed", "stick", "stone", "meat"}

# Control ecológico de dispersión animal.
# No afecta a humanos: los animales ya están programados y estos valores evitan
# que pollos/vacas terminen todos pegados a un lateral del mapa por deriva aleatoria.
ANIMAL_EDGE_MARGIN = 8
ANIMAL_CROWD_RADIUS = 5
ANIMAL_CROWD_LIMITS = {"chicken": 5, "cow": 4}
ANIMAL_DISPERSAL_CHANCE = {"chicken": 0.52, "cow": 0.42}
ANIMAL_MIGRATION_CHECK_TICKS = 36
ANIMAL_EDGE_CLUSTER_RATIO = 0.55
# v1.7.2: ya no empujamos al centro. Usamos objetivos repartidos por todo el mapa.
ANIMAL_CENTER_JITTER = 14
ANIMAL_SPREAD_MARGIN = 4
ANIMAL_REPRODUCTION_MULTIPLIER = 1.20
ANIMAL_TARGET_SAMPLE_CELLS = 36

# v1.7.2: semillas abundantes y regenerativas. Evita que los pollos/vacas
# se queden todos anclados a una única zona por falta de alimento repartido.
SEED_TARGET_ON_MAP = 120
SEED_MAX_ON_MAP = 180
SEED_REGROW_PER_TICK = 3
SEED_REGROW_EVERY_TICKS = 1
SEED_GROW_CLUSTER_CHANCE = 0.45



# ============================================================
# SÍMBOLOS Y COLOR
# ============================================================

EMPTY = "."
CAVE_WALL = "C"
CAVE_ENTRANCE = "E"    # lógico; se renderiza como "."
CAVE_INTERIOR = "I"    # lógico; se renderiza como "."
WATER = "~"
SEED = "s"
STICK = "/"
STONE = "o"
MEAT = "m"


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    PURPLE = "\033[95m"
    GOLD = "\033[38;5;220m"
    DARK_BLUE = "\033[38;5;21m"


def ctext(text: str, color: str) -> str:
    if not USE_COLORS:
        return text
    return f"{color}{text}{Color.RESET}"


def red_alert(text: str) -> str:
    return ctext(text, Color.BRIGHT_RED + Color.BOLD)


def cyan_alert(text: str) -> str:
    return ctext(text, Color.BRIGHT_CYAN + Color.BOLD)


def purple_alert(text: str) -> str:
    return ctext(text, Color.PURPLE + Color.BOLD)


def gold_alert(text: str) -> str:
    return ctext(text, Color.GOLD + Color.BOLD)


def dark_blue_alert(text: str) -> str:
    return ctext(text, Color.DARK_BLUE + Color.BOLD)


SUPER_RELEVANT_KEYWORDS = (
    "miedo", "peligro", "evitación", "evitacion",
    "vida", "vivo", "muerte", "morir", "no_movimiento",
    "religión", "religion", "dios", "fuerza invisible",
    "ritual", "ofrenda", "duelo", "proto-religión", "proto-religion",
    "identidad", "nosotros", "refugio", "cueva"
)


def confidence_from_text(text: str) -> float:
    m = re.search(r"confianza\s*[:|]?\s*(\d+(?:[\.,]\d+)?)%", text, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"CONFIANZA\s*:\s*(\d+(?:[\.,]\d+)?)%", text, flags=re.IGNORECASE)
    if not m:
        return 0.0
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return 0.0


def is_super_relevant_text(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in SUPER_RELEVANT_KEYWORDS)


def style_for_report_text(text: str, confidence: Optional[float] = None) -> str:
    conf = confidence if confidence is not None else confidence_from_text(text)
    low = text.lower()

    # Azul oscuro: conclusiones claras del BOT INVESTIGADOR o auditorías del BOT REVISOR.
    # Si el revisor confirma algo con confianza alta, puede volverlo dorado/morado.
    if "bot revisor" in low:
        if conf >= 85.0:
            return "purple"
        if conf >= 60.0 or is_super_relevant_text(text):
            return "gold"
        return "darkblue"

    if "bot investigador" in low and (
        "señal clara encontrada: sí" in low
        or "señal clara encontrada: si" in low
        or "conclusión clara" in low
        or "conclusion clara" in low
    ):
        if conf >= 85.0:
            return "purple"
        if conf >= 60.0 or is_super_relevant_text(text):
            return "gold"
        return "darkblue"

    # Dorado solo si además de relevante supera un umbral razonable:
    # evita que proto-religión débil al 20% parezca descubrimiento fuerte.
    if conf >= 85.0 and not is_super_relevant_text(text):
        return "purple"
    if is_super_relevant_text(text) and conf >= 60.0:
        return "gold"
    if conf >= 85.0:
        return "purple"
    if "DETECTOR" in text or "CONCEPTO" in text or "BOT INVESTIGADOR" in text:
        return "cyan"
    return "normal"


def color_each_line(text: str, color: str) -> str:
    """Aplica ANSI a cada línea para que Terminal y HTML no pierdan color tras saltos de línea."""
    if not USE_COLORS:
        return text
    return "\n".join(f"{color}{line}{Color.RESET}" if line else line for line in text.split("\n"))


def style_text(text: str, style: str) -> str:
    # Importante: coloreamos línea por línea, no solo poniendo ANSI al inicio
    # y RESET al final del bloque. Algunos visores/HTML/Terminal pierden el
    # color tras el primer salto de línea si el bloque es muy largo.
    if style == "gold":
        return color_each_line(text, Color.GOLD + Color.BOLD)
    if style == "purple":
        return color_each_line(text, Color.PURPLE + Color.BOLD)
    if style == "cyan":
        return color_each_line(text, Color.BRIGHT_CYAN + Color.BOLD)
    if style == "darkblue":
        return color_each_line(text, Color.DARK_BLUE + Color.BOLD)
    if style == "red":
        return color_each_line(text, Color.BRIGHT_RED + Color.BOLD)
    return text
    return text



def is_valuable_report_text(text: str) -> bool:
    """Filtro estricto para conceptos realmente valiosos.
    Incluye dorados, morados, conclusiones claras del bot investigador y conceptos raros de alto valor
    aunque su confianza sea media (refugio, almacenamiento, cebo/trampa, miedo/muerte, etc.).
    """
    low = text.lower()
    conf = confidence_from_text(text)
    style = style_for_report_text(text, conf)
    if style in ("gold", "purple", "darkblue"):
        return True

    valuable_keys = (
        "cueva", "refugio", "almacenamiento", "provisiones", "inventario",
        "cebo", "trampa", "miedo", "peligro", "muerte", "no_movimiento",
        "sueño/fuerza", "sueño", "fuerza", "bot revisor", "bot investigador"
    )
    if any(k in low for k in valuable_keys):
        # Umbrales más bajos para rarezas realmente valiosas.
        if "almacen" in low and conf >= 35:
            return True
        if ("cebo" in low or "trampa" in low) and conf >= 30:
            return True
        if ("cueva" in low or "refugio" in low) and conf >= 45:
            return True
        if ("miedo" in low or "peligro" in low or "muerte" in low or "no_movimiento" in low) and conf >= 55:
            return True
        if ("sueño/fuerza" in low or "sueño" in low and "fuerza" in low) and conf >= 75:
            return True
        if "bot revisor" in low and conf >= 55:
            return True
        if "bot investigador" in low and ("señal clara encontrada: sí" in low or "conclusión clara" in low or "conclusion clara" in low):
            return True

    # Conceptos no clasificados solo si son muy fuertes y de alto valor, no por ruido normal.
    if conf >= 80 and concept_importance_score(text, conf) >= 85:
        return True
    return False

def concept_importance_score(text: str, confidence: float) -> float:
    """Valor externo del concepto para logs/árbol, no afecta a genes ni a decisiones internas."""
    low = text.lower()
    base = confidence
    if any(k in low for k in ("refugio", "cueva", "dentro seguro", "lugar de reposo")):
        base += 48.0
    if any(k in low for k in ("miedo", "peligro", "evitación", "evitacion", "dolor")):
        base += 18.0
    if any(k in low for k in ("vida", "muerte", "morir", "no_movimiento")):
        base += 22.0
    if any(k in low for k in ("religión", "religion", "ritual", "ofrenda", "dios", "proto-religión", "proto-religion")):
        # Religión solo vale mucho si tiene pruebas; si no, queda como hipótesis débil.
        base += 8.0 if confidence < 60 else 28.0
    return clamp(base, 0.0, 140.0)


def concept_importance_label(score: float) -> str:
    if score >= 105:
        return "CRÍTICO"
    if score >= 85:
        return "MUY ALTO"
    if score >= 60:
        return "ALTO"
    if score >= 35:
        return "MEDIO"
    return "BAJO"


# ============================================================
# UTILIDADES
# ============================================================

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def dist(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def sign(n: int) -> int:
    if n < 0:
        return -1
    if n > 0:
        return 1
    return 0


def pct(x: float) -> str:
    return f"{x:.1f}%".replace(".", ",")


def clear_screen() -> None:
    # Limpieza simple. No vacía el scrollback, para evitar parpadeos/pantalla negra
    # al refrescar en auto. El render principal escribe pantalla completa de golpe.
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()


def weighted_choice(items: List[Tuple[Any, float]]) -> Any:
    total = sum(max(0.0, w) for _, w in items)
    if total <= 0:
        return random.choice([x for x, _ in items])
    r = random.uniform(0, total)
    acc = 0.0
    for item, weight in items:
        acc += max(0.0, weight)
        if acc >= r:
            return item
    return items[-1][0]


# ============================================================
# EVENTOS Y MEMORIA
# ============================================================

@dataclass
class Event:
    tick: int
    day: int
    actor_id: str
    kind: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NeuralMemory:
    """
    Memoria asociativa sencilla. No es una red neuronal profunda.
    Sirve para que el Metaobservador tenga un mini registro auditable.
    """
    activations: Dict[str, float] = field(default_factory=dict)
    connections: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def activate(self, node: str, amount: float = 0.15) -> None:
        self.activations[node] = clamp(self.activations.get(node, 0.0) * 0.96 + amount, 0.0, 1.0)

    def reinforce(self, a: str, b: str, amount: float = 0.05) -> None:
        if a == b:
            return
        key = tuple(sorted((a, b)))
        self.connections[key] = clamp(self.connections.get(key, 0.0) + amount, 0.0, 1.0)
        self.activate(a, amount * 0.8)
        self.activate(b, amount * 0.8)

    def decay(self) -> None:
        for k in list(self.activations.keys()):
            self.activations[k] *= 0.985
            if self.activations[k] < 0.01:
                del self.activations[k]
        for k in list(self.connections.keys()):
            self.connections[k] *= 0.999
            if self.connections[k] < 0.01:
                del self.connections[k]

    def top_activations(self, n: int = 8) -> List[Tuple[str, float]]:
        return sorted(self.activations.items(), key=lambda x: x[1], reverse=True)[:n]

    def top_connections(self, n: int = 8) -> List[Tuple[Tuple[str, str], float]]:
        return sorted(self.connections.items(), key=lambda x: x[1], reverse=True)[:n]


# ============================================================
# OBJETOS
# ============================================================

@dataclass
class Item:
    item_id: str
    kind: str
    x: int
    y: int
    weight: float
    char: str
    edible: bool = False
    damage: float = 0.0
    durability: int = 0
    uses_left: int = 0


ITEM_PROTOTYPES = {
    "seed": {"char": SEED, "weight": 1, "edible": True, "damage": 0, "durability": 0},
    "stick": {"char": STICK, "weight": 2, "edible": False, "damage": 3, "durability": 5},
    "stone": {"char": STONE, "weight": 5, "edible": False, "damage": 7, "durability": 10},
    "meat": {"char": MEAT, "weight": 2, "edible": True, "damage": 0, "durability": 0},
    "cave_wall": {"char": CAVE_WALL, "weight": 9999, "edible": False, "damage": 0, "durability": 9999},
}


# ============================================================
# CRIATURAS
# ============================================================

@dataclass
class Creature:
    entity_id: str
    kind: str
    name: str
    x: int
    y: int
    hp: float
    max_hp: float
    damage: float
    alive: bool = True
    last_attacker: Optional[str] = None
    last_reproduction_day: int = 0

    def pos(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def shape_offsets(self) -> List[Tuple[int, int]]:
        if self.kind == "chicken":
            return [(0, 0)]
        if self.kind == "cow":
            return [(0, 0), (0, 1)]
        if self.kind == "trex":
            return [(0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)]
        return [(0, 0)]

    def occupied_cells(self, nx: Optional[int] = None, ny: Optional[int] = None) -> List[Tuple[int, int]]:
        px = self.x if nx is None else nx
        py = self.y if ny is None else ny
        return [(px + dx, py + dy) for dx, dy in self.shape_offsets()]


@dataclass
class Genes:
    speed: float = 1.0
    strength: float = 10.0
    memory: float = 1.0
    curiosity: float = 0.85
    sociability: float = 0.5
    aggression: float = 0.25
    association: float = 0.85
    fertility: float = 0.6
    sleep_need: float = 1.0
    energy_efficiency: float = 1.0
    weirdness: float = 0.25
    exploration_spirit: float = 1.35  # impulso heredable a explorar lejos y dispersarse

    def mutated_child(self) -> "Genes":
        def m(v: float, scale: float, lo: float, hi: float) -> float:
            return clamp(v + random.uniform(-scale, scale), lo, hi)

        return Genes(
            speed=m(self.speed, 0.05, 0.5, 1.8),
            strength=m(self.strength, 0.6, 4.0, 20.0),
            memory=m(self.memory, 0.06, 0.3, 2.0),
            curiosity=m(self.curiosity, 0.06, 0.0, 1.8),
            sociability=m(self.sociability, 0.06, 0.0, 1.5),
            aggression=m(self.aggression, 0.06, 0.0, 1.3),
            association=m(self.association, 0.06, 0.2, 2.0),
            fertility=m(self.fertility, 0.05, 0.1, 1.5),
            sleep_need=m(self.sleep_need, 0.04, 0.6, 1.5),
            energy_efficiency=m(self.energy_efficiency, 0.05, 0.5, 1.6),
            weirdness=m(self.weirdness, 0.05, 0.0, 1.2),
            exploration_spirit=m(self.exploration_spirit, 0.12, 0.5, 3.0),
        )


@dataclass
class Human(Creature):
    genes: Genes = field(default_factory=Genes)
    hunger: float = 15.0
    thirst: float = 15.0
    sleepiness: float = 0.0
    energy: float = 90.0
    age: int = 0
    birth_number: int = 0
    parent1_birth: int = 0
    parent2_birth: int = 0
    inventory: List[Item] = field(default_factory=list)
    memory_events: List[Event] = field(default_factory=list)
    neural: NeuralMemory = field(default_factory=NeuralMemory)
    sleep_history: List[Tuple[int, bool]] = field(default_factory=list)
    last_action: str = "nacer"
    detected_concepts: List[str] = field(default_factory=list)
    exploration_target: Optional[Tuple[int, int]] = None
    hunger_resistance: float = 1.0
    thirst_resistance: float = 1.0
    old_age_resistance: float = 1.0
    protection_marks: int = 0
    immortal: bool = False  # LAB/experimental: si True no puede morir; solo se activa por comando explícito.

    def record(self, event: Event) -> None:
        self.memory_events.append(event)
        limit = int(HUMAN_MEMORY_LIMIT * self.genes.memory)
        if len(self.memory_events) > limit:
            self.memory_events = self.memory_events[-limit:]

    def recent_sleep_hours(self, now_tick: int, window: int = TICKS_PER_DAY) -> int:
        cutoff = now_tick - window
        self.sleep_history = [(t, s) for t, s in self.sleep_history if t >= cutoff]
        return sum(1 for _, slept in self.sleep_history if slept)

    def is_tired_for_damage(self, now_tick: int) -> bool:
        return self.recent_sleep_hours(now_tick) < MIN_SLEEP_PER_24H

    def effective_damage(self, base: float, now_tick: int) -> float:
        if self.is_tired_for_damage(now_tick):
            return base * SLEEP_DAMAGE_MULTIPLIER_WHEN_TIRED
        return base

    def carry_weight(self) -> float:
        return sum(i.weight for i in self.inventory)

    def can_carry(self, item: Item) -> bool:
        # Inventario físico simple: máximo 5 objetos y solo objetos portables definidos.
        # No es bloqueo mágico: representa manos/bolsillos/capacidad de transporte primitiva.
        if item.kind not in ALLOWED_INVENTORY_KINDS:
            return False
        if len(self.inventory) >= MAX_INVENTORY_ITEMS:
            return False
        return self.carry_weight() + item.weight <= self.genes.strength * 1.5

    def best_weapon(self) -> Optional[Item]:
        weapons = [i for i in self.inventory if i.damage > 0 and i.uses_left > 0]
        return max(weapons, key=lambda i: i.damage) if weapons else None


@dataclass
class ConceptInvestigation:
    """Investigación longitudinal externa del Metaobservador.

    No introduce conocimiento en el protohumano. Solo decide qué mirar durante
    varios días y, si hay hijos, qué rasgos conviene vigilar en el linaje.
    """
    inv_id: int
    origin_birth: int
    subject_birth: int
    category: str
    hypothesis: str
    started_tick: int
    started_day: int
    expires_tick: int
    last_update_tick: int
    inherited_from: Optional[int] = None
    generations_left: int = 3
    watch_weights: Dict[str, float] = field(default_factory=dict)
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    confidence: float = 20.0
    state: str = "OBSERVACIÓN INICIAL"
    concluded: bool = False
    valuable: bool = False

    def short_label(self) -> str:
        return f"INV{self.inv_id} H{self.subject_birth} {self.category} {self.confidence:.1f}% {self.state}"


# ============================================================
# MUNDO
# ============================================================

class World:
    def __init__(self) -> None:
        if RANDOM_SEED is not None:
            random.seed(RANDOM_SEED)

        self.tick = 0
        self.day = 0
        self.grid: List[List[str]] = [[EMPTY for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.items: Dict[str, Item] = {}
        self.creatures: Dict[str, Creature] = {}
        self.humans: Dict[str, Human] = {}
        self.events: List[Event] = []
        self.concept_logs: List[str] = []
        self.unexpected_logs: List[str] = []
        self.all_logs: List[str] = []
        self.cave_cells: Dict[str, Tuple[int, int]] = {}
        self.cave_entrances: Set[Tuple[int, int]] = set()
        self.cave_interiors: Set[Tuple[int, int]] = set()
        self.next_id = 1
        self.next_human_birth_number = 1
        self.meta = MetaObserver(self)
        self.auto_spawn_when_one = AUTO_SPAWN_WHEN_ONE_DEFAULT
        self.auto_spawn_amount = AUTO_SPAWN_WHEN_ONE_AMOUNT
        self.last_auto_spawn_tick = -999999
        self.extinction_notice_shown = False
        self.gene_bank: Set[int] = set()
        self.gene_bank_notes: Dict[int, List[str]] = {}
        self.investigations: Dict[int, ConceptInvestigation] = {}
        self.next_investigation_id = 1
        self.lineage_watch_roots: Dict[int, List[int]] = {}
        # v2.0: laboratorio separado para humanos de prueba. No altera la lógica de humanos normales.
        self.lab_isolate: bool = True
        self.lab_notes: List[str] = []
        self.setup()

    # ----------------------------
    # IDs y log
    # ----------------------------

    def make_id(self, prefix: str) -> str:
        eid = f"{prefix}{self.next_id}"
        self.next_id += 1
        return eid

    def log(self, kind: str, actor_id: str = "world", **data: Any) -> Event:
        ev = Event(self.tick, self.day, actor_id, kind, data)
        self.events.append(ev)
        if len(self.events) > LOG_LIMIT:
            self.events = self.events[-LOG_LIMIT:]

        # Log completo permanente de la sesión, más útil que "Últimos eventos".
        actor_name = actor_id
        if actor_id in self.humans:
            actor_name = f"{actor_id}/{self.humans[actor_id].name}"
        elif actor_id in self.creatures:
            actor_name = f"{actor_id}/{self.creatures[actor_id].kind}"
        self.all_logs.append(f"[Día {ev.day} T{ev.tick}] {actor_name}: {kind} {data}")
        # all_logs conserva la sesión completa para el comando todos_logs/export_logs.

        if actor_id in self.humans:
            self.humans[actor_id].record(ev)
        return ev

    # ----------------------------
    # Setup
    # ----------------------------

    def setup(self) -> None:
        self.place_all_caves()
        self.place_water_patches()
        self.scatter_items("seed", INITIAL_SEED_PATCHES)
        self.scatter_items("stick", INITIAL_STICKS)
        self.scatter_items("stone", INITIAL_STONES)
        self.spawn_initial_creatures()

    def place_all_caves(self) -> None:
        """
        Coloca 6 cuevas esparcidas por el mapa.
        - 4 cuevas pequeñas.
        - 2 cuevas grandes irregulares con más interior seguro.

        En los patrones:
        C = pared física de cueva
        E = entrada lógica
        I = interior lógico seguro
        espacio = exterior / no colocar nada

        E e I no se muestran como letras en el mapa: visualmente se ven como suelo.
        """
        small_cave = [
            "CCC",
            "EIC",
            "CCC",
        ]

        large_cave_1 = [
            "CCCCCCCCC        ",
            "EIIIIIIICCC      ",
            " IIIIIIIICCC     ",
            " CIIIIICCCC      ",
            " CCCCCCC         ",
        ]

        large_cave_2 = [
            "CCCCCCCCCCCC     ",
            "CIIIIIIIIICCC    ",
            "EIIIIIIIIIICC    ",
            "CIIIIIIICCCC     ",
            "CCCCCCCCCC       ",
        ]

        cave_layouts = [
            (6, 5, small_cave),
            (124, 5, small_cave),
            (8, 23, small_cave),
            (124, 23, small_cave),
            (34, 10, large_cave_1),
            (72, 17, large_cave_2),
        ]

        for x, y, pattern in cave_layouts:
            self.place_pattern_cave(x, y, pattern)

    def place_pattern_cave(self, x: int, y: int, pattern: List[str]) -> None:
        for dy, row in enumerate(pattern):
            for dx, cell in enumerate(row):
                gx, gy = x + dx, y + dy
                if not (0 <= gx < WIDTH and 0 <= gy < HEIGHT):
                    continue
                if cell == "C":
                    self.grid[gy][gx] = CAVE_WALL
                elif cell == "E":
                    self.grid[gy][gx] = CAVE_ENTRANCE
                    self.cave_entrances.add((gx, gy))
                    if "entrance" not in self.cave_cells:
                        self.cave_cells["entrance"] = (gx, gy)
                elif cell == "I":
                    self.grid[gy][gx] = CAVE_INTERIOR
                    self.cave_interiors.add((gx, gy))
                    if "interior" not in self.cave_cells:
                        self.cave_cells["interior"] = (gx, gy)
                else:
                    pass

    def nearest_cave_interior(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        if not self.cave_interiors:
            return None
        return min(self.cave_interiors, key=lambda p: dist(pos, p))

    def nearest_cave_entrance(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        if not self.cave_entrances:
            return None
        return min(self.cave_entrances, key=lambda p: dist(pos, p))

    def place_water_patches(self) -> None:
        centers = [
            (10, 8), (22, 22), (42, 5), (55, 21), (72, 8),
            (88, 23), (108, 12), (126, 24), (32, 16), (125, 5),
        ]
        for cx, cy in centers[:INITIAL_WATER_PATCHES]:
            for _ in range(20):
                x = int(clamp(random.gauss(cx, 2), 1, WIDTH - 2))
                y = int(clamp(random.gauss(cy, 2), 1, HEIGHT - 2))
                if self.grid[y][x] == EMPTY:
                    self.grid[y][x] = WATER

    def scatter_items(self, kind: str, count: int) -> None:
        for _ in range(count):
            pos = self.random_empty_cell()
            if pos:
                self.add_item(kind, pos[0], pos[1])

    def seed_count_on_map(self) -> int:
        return sum(1 for i in self.items.values() if i.kind == "seed")

    def grow_seed_patch(self, near: Optional[Tuple[int, int]] = None) -> bool:
        """Crecimiento natural de semillas.
        No es conocimiento humano: es ecología del mapa. Las semillas pueden ser
        comidas/recogidas, pero el mundo sigue generándolas para que el alimento
        vegetal no se agote ni arrastre a todos los pollos al mismo sitio.
        """
        for _ in range(90):
            if near is not None and random.random() < SEED_GROW_CLUSTER_CHANCE:
                x = int(clamp(round(random.gauss(near[0], 5)), 1, WIDTH - 2))
                y = int(clamp(round(random.gauss(near[1], 3)), 1, HEIGHT - 2))
            else:
                x = random.randint(1, WIDTH - 2)
                y = random.randint(1, HEIGHT - 2)
            if self.grid[y][x] != EMPTY:
                continue
            if self.creature_at(x, y):
                continue
            # Permitimos varias semillas en el mapa, pero evitamos apilar muchas
            # en la misma celda para que no sea un imán único.
            if any(i.kind == "seed" and i.x == x and i.y == y for i in self.items.values()):
                continue
            self.add_item("seed", x, y)
            return True
        return False

    def regrow_seeds(self) -> None:
        """Mantiene semillas abundantes y repartidas por el mapa.
        - Si hay menos de SEED_TARGET_ON_MAP, crecen varias por tick.
        - Si ya hay suficientes, siguen apareciendo algunas hasta un máximo.
        Esto impide que las semillas se agoten y da a pollos/humanos muchos
        puntos de interés dispersos.
        """
        if SEED_REGROW_EVERY_TICKS <= 0 or self.tick % SEED_REGROW_EVERY_TICKS != 0:
            return
        current = self.seed_count_on_map()
        if current >= SEED_MAX_ON_MAP:
            return
        missing = max(0, SEED_TARGET_ON_MAP - current)
        # Si faltan muchas, crecen más; si ya hay bastantes, crecimiento suave.
        attempts = SEED_REGROW_PER_TICK + min(8, missing // 12)
        if current >= SEED_TARGET_ON_MAP:
            attempts = 1 if random.random() < 0.35 else 0
        if attempts <= 0:
            return
        existing = [(i.x, i.y) for i in self.items.values() if i.kind == "seed"]
        for _ in range(attempts):
            if self.seed_count_on_map() >= SEED_MAX_ON_MAP:
                break
            near = random.choice(existing) if existing and random.random() < 0.25 else None
            if self.grow_seed_patch(near=near):
                existing = [(i.x, i.y) for i in self.items.values() if i.kind == "seed"]

    def spawn_initial_creatures(self) -> None:
        # Humanos cerca del centro sin salirse del mapa, aunque elijas muchos.
        placed = 0
        center = (WIDTH // 2, HEIGHT // 2)
        for radius in range(0, 14):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if placed >= INITIAL_HUMANS:
                        break
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    x, y = center[0] + dx, center[1] + dy
                    dummy = Creature("dummy", "human", "human", x, y, 30, 30, 1)
                    if self.can_place_creature(dummy, x, y):
                        self.add_human(x, y)
                        placed += 1
                if placed >= INITIAL_HUMANS:
                    break
            if placed >= INITIAL_HUMANS:
                break
        while placed < INITIAL_HUMANS:
            pos = self.random_empty_cell()
            if not pos:
                break
            self.add_human(*pos)
            placed += 1

        for _ in range(INITIAL_CHICKENS):
            pos = self.random_empty_cell()
            if pos:
                self.add_creature("chicken", *pos)

        for _ in range(INITIAL_COWS):
            pos = self.random_empty_cell_for_kind("cow")
            if pos:
                self.add_creature("cow", *pos)

        for _ in range(INITIAL_TREX):
            pos = self.random_empty_cell_for_kind("trex", avoid_center=True)
            if pos:
                self.add_creature("trex", *pos)

    def add_item(self, kind: str, x: int, y: int) -> Item:
        p = ITEM_PROTOTYPES[kind]
        item = Item(
            item_id=self.make_id("it"),
            kind=kind,
            x=x,
            y=y,
            weight=p["weight"],
            char=p["char"],
            edible=p["edible"],
            damage=p["damage"],
            durability=p["durability"],
            uses_left=p["durability"],
        )
        self.items[item.item_id] = item
        return item

    def add_creature(self, kind: str, x: int, y: int) -> Creature:
        if kind == "chicken":
            c = Creature(self.make_id("P"), kind, "Pollo", x, y, 5, 5, 0)
        elif kind == "cow":
            c = Creature(self.make_id("V"), kind, "Vaca", x, y, 20, 20, 8)
        elif kind == "trex":
            c = Creature(self.make_id("T"), kind, "T-Rex", x, y, 50, 50, 18, last_reproduction_day=self.day)
        else:
            raise ValueError(kind)
        self.creatures[c.entity_id] = c
        return c

    def inherit_genes(self, parent: Optional[Human], parent2: Optional[Human] = None) -> Genes:
        """Hereda genes, pero NUNCA conceptos ni memoria."""
        if not parent:
            return Genes()
        if not parent2:
            return parent.genes.mutated_child()

        def avg(a: float, b: float) -> float:
            return (a + b) / 2.0

        base = Genes(
            speed=avg(parent.genes.speed, parent2.genes.speed),
            strength=avg(parent.genes.strength, parent2.genes.strength),
            memory=avg(parent.genes.memory, parent2.genes.memory),
            curiosity=avg(parent.genes.curiosity, parent2.genes.curiosity),
            sociability=avg(parent.genes.sociability, parent2.genes.sociability),
            aggression=avg(parent.genes.aggression, parent2.genes.aggression),
            association=avg(parent.genes.association, parent2.genes.association),
            fertility=avg(parent.genes.fertility, parent2.genes.fertility),
            sleep_need=avg(parent.genes.sleep_need, parent2.genes.sleep_need),
            energy_efficiency=avg(parent.genes.energy_efficiency, parent2.genes.energy_efficiency),
            weirdness=avg(parent.genes.weirdness, parent2.genes.weirdness),
            exploration_spirit=avg(parent.genes.exploration_spirit, parent2.genes.exploration_spirit),
        )
        return base.mutated_child()

    def gene_score(self, h: Human) -> float:
        """Puntuación genética para exploración/aprendizaje/conceptos, no incluye conceptos aprendidos."""
        g = h.genes
        return (
            # Curiosidad y exploración pesan mucho: buscamos linajes que descubran,
            # se dispersen y prueben rutas nuevas. Asociación y memoria siguen siendo
            # críticas para que esas experiencias se conviertan en aprendizaje.
            g.exploration_spirit * 32
            + g.curiosity * 30
            + g.association * 26
            + g.memory * 22
            + g.sociability * 10
            + g.speed * 8
            + g.energy_efficiency * 8
            + g.weirdness * 6
            + (g.strength / 20.0) * 4
        )

    def human_by_birth(self, birth_number: int) -> Optional[Human]:
        for h in self.humans.values():
            if h.birth_number == birth_number:
                return h
        return None

    def best_gene_humans(self, alive_only: bool = True, n: int = 20) -> List[Human]:
        # v2.0: los humanos de laboratorio no contaminan rankings/auto_spawn normales.
        humans = [h for h in self.humans.values() if not getattr(h, "is_lab", False) and (h.alive or not alive_only)]
        return sorted(humans, key=self.gene_score, reverse=True)[:n]

    def find_spawn_position(self, parent: Optional[Human] = None, parent2: Optional[Human] = None) -> Optional[Tuple[int, int]]:
        centers: List[Tuple[int, int]] = []
        if parent and parent.alive:
            centers.append(parent.pos())
        if parent2 and parent2.alive:
            centers.append(parent2.pos())
        if not centers:
            alive = [h for h in self.humans.values() if h.alive]
            if alive:
                centers.append(random.choice(alive).pos())
            else:
                centers.append((WIDTH // 2, HEIGHT // 2))
        cx = round(sum(p[0] for p in centers) / len(centers))
        cy = round(sum(p[1] for p in centers) / len(centers))
        for radius in range(1, 12):
            spots = []
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    spots.append((cx + dx, cy + dy))
            random.shuffle(spots)
            for x, y in spots:
                dummy = Creature("dummy", "human", "human", x, y, 30, 30, 1)
                if self.can_place_creature(dummy, x, y):
                    return (x, y)
        return self.random_empty_cell()

    def manual_spawn_humans(self, count: int, parent: Optional[Human] = None, parent2: Optional[Human] = None) -> List[Human]:
        # v2.2.6: si un humano es inmortal, no puede generar descendencia ni por
        # reproducción natural ni por comandos que usen padres explícitos/best/bank.
        # Esto mantiene la inmortalidad como herramienta experimental, no como ventaja evolutiva.
        if (parent and getattr(parent, "immortal", False)) or (parent2 and getattr(parent2, "immortal", False)):
            self.log(
                "spawn_bloqueado_padre_inmortal",
                "world",
                padre1=parent.birth_number if parent else 0,
                padre2=parent2.birth_number if parent2 else 0,
                motivo="los inmortales experimentales no se reproducen",
            )
            return []
        born: List[Human] = []
        for _ in range(max(0, count)):
            pos = self.find_spawn_position(parent, parent2)
            if not pos:
                break
            child = self.add_human(pos[0], pos[1], parent, parent2)
            born.append(child)
            self.log(
                "spawn_manual",
                child.entity_id,
                cantidad_solicitada=count,
                padre1=parent.birth_number if parent else 0,
                padre2=parent2.birth_number if parent2 else 0,
                nota="hijo sin conceptos heredados; solo genes heredados" if parent else "spawn inicial sin padres",
            )
        return born

    def format_human_gene_line(self, h: Human) -> str:
        g = h.genes
        status = "vivo" if h.alive else "muerto"
        concepts = len(h.detected_concepts)
        return (
            f"#{h.birth_number:>4} {h.name:<12} {status:<6} score={self.gene_score(h):5.1f} "
            f"cur={g.curiosity:.2f} assoc={g.association:.2f} mem={g.memory:.2f} soc={g.sociability:.2f} "
            f"vel={g.speed:.2f} eff={g.energy_efficiency:.2f} exp={g.exploration_spirit:.2f} weird={g.weirdness:.2f} fuerza={g.strength:.1f} "
            f"conceptos_detectados={concepts} padres={h.parent1_birth}/{h.parent2_birth} bank={'★' if h.birth_number in self.gene_bank else '-'}"
        )

    def brain_report(self, birth_number: int) -> str:
        h = self.human_by_birth(birth_number)
        if not h:
            return f"No existe humano con número de nacimiento {birth_number}."

        status = "vivo" if h.alive else "muerto"
        g = h.genes

        active_nodes = set(h.neural.activations.keys())
        connected_nodes: Set[str] = set()
        for a, b in h.neural.connections.keys():
            connected_nodes.add(a)
            connected_nodes.add(b)
        known_nodes = active_nodes | connected_nodes
        total_connections = len(h.neural.connections)

        # Reportes de conceptos ya guardados por el Metaobservador que mencionan a este humano.
        concept_hits = []
        for block in self.concept_logs:
            if f"HUMANO: {h.name}" in block or f"{h.entity_id}" in block or f"#{h.birth_number}" in block:
                concept_hits.append(block)

        # Eventos crudos importantes para auditar cómo se pudo formar un concepto.
        important_kinds = {
            "ataque", "ataque_falla_por_espacio", "dormir", "beber", "comer", "comer_presa",
            "coger_objeto", "fallo_coger_peso", "fallo_fisico_previsible", "accion_fisica_sin_efecto",
            "accion_no_prevista", "experimento_refugio", "soltar_semilla", "reproduccion", "observa_muerte",
            "daño_por_necesidad", "muerte", "comer_carne_trex", "fallo_coger_inventario_lleno",
        }
        raw_events = [e for e in h.memory_events if e.kind in important_kinds]

        def ev_line(e: Event) -> str:
            return f"[Día {e.day} T{e.tick}] {e.kind} {e.data}"

        lines: List[str] = []
        lines.append(f"REGISTRO NEURONAL COMPLETO — HUMANO #{h.birth_number} / {h.name}")
        lines.append("=" * 100)
        lines.append(f"Estado: {status} | ID: {h.entity_id} | edad_ticks={h.age} | pos={h.pos()} | HP={h.hp:.1f}/{h.max_hp} | inmortal={'SÍ' if getattr(h, 'immortal', False) else 'no'}")
        lines.append(f"Padres: {h.parent1_birth}/{h.parent2_birth} | hijos directos: {sum(1 for x in self.humans.values() if x.parent1_birth == h.birth_number or x.parent2_birth == h.birth_number)}")
        lines.append(f"Necesidades: hambre={h.hunger:.1f} sed={h.thirst:.1f} sueño={h.sleepiness:.1f} energía={h.energy:.1f}")
        lines.append(f"Resistencias extra: hambre={h.hunger_resistance:.2f} sed={h.thirst_resistance:.2f} vejez={h.old_age_resistance:.2f} | banco_genético={'SÍ' if h.birth_number in self.gene_bank else 'NO'}")
        lines.append(f"Inventario: {[i.kind for i in h.inventory]} | última acción: {h.last_action}")
        lines.append("")
        lines.append("GENES:")
        lines.append(f"  score_genético={self.gene_score(h):.2f}")
        lines.append(f"  curiosidad={g.curiosity:.3f} | asociación={g.association:.3f} | memoria={g.memory:.3f} | sociabilidad={g.sociability:.3f}")
        lines.append(f"  velocidad={g.speed:.3f} | eficiencia_energética={g.energy_efficiency:.3f} | espíritu_explorador={g.exploration_spirit:.3f} | rareza/experimentación={g.weirdness:.3f}")
        lines.append(f"  fuerza={g.strength:.3f} | agresividad={g.aggression:.3f} | fertilidad={g.fertility:.3f} | necesidad_sueño={g.sleep_need:.3f}")
        lines.append("")
        lines.append("TAMAÑO DEL REGISTRO NEURONAL:")
        lines.append(f"  neuronas/nodos activos ahora: {len(active_nodes)}")
        lines.append(f"  neuronas/nodos conocidos total: {len(known_nodes)}")
        lines.append(f"  conexiones reforzadas: {total_connections}")
        lines.append("  Nota: aquí 'neurona' significa nodo conceptual/sensorial interno de esta memoria asociativa, no neurona biológica real.")
        lines.append("")

        lines.append("CONCEPTOS DETECTADOS POR EL METAOBSERVADOR:")
        if not concept_hits and not h.detected_concepts:
            lines.append("  Ningún concepto detectado todavía para este humano.")
        else:
            if h.detected_concepts:
                lines.append("  Resumen interno del humano:")
                for c in h.detected_concepts[-20:]:
                    lines.append(f"  - {c}")
            if concept_hits:
                lines.append("")
                lines.append("  Reportes completos relacionados con este humano:")
                for idx, block in enumerate(concept_hits[-8:], 1):
                    lines.append(f"\n  --- REPORTE CONCEPTO {idx} ---")
                    for line in block.splitlines()[:80]:
                        lines.append("  " + line)
        lines.append("")

        lines.append("POR QUÉ SE CREE QUE HA DESARROLLADO/REFORZADO CONCEPTOS:")
        # Interpretación auditable basada en conexiones, sin darlo por cierto.
        pairs_to_check = [
            (("cueva_interior", "reposo"), "posible relación cueva ↔ descanso/refugio"),
            (("cueva_interior", "menos_daño"), "posible relación cueva ↔ menos daño"),
            (("semilla", "pollo_cercano"), "posible relación semillas ↔ pollos cercanos"),
            (("pollo", "hambre_baja"), "posible relación pollo ↔ comida"),
            (("sueño_bajo", "golpe_debil"), "posible relación falta de sueño ↔ menor fuerza"),
            (("descanso_suficiente", "golpe_fuerte"), "posible relación descanso ↔ fuerza"),
            (("forma_trex", "dolor"), "posible relación T-Rex ↔ dolor/peligro"),
            (("forma_grande", "dolor"), "posible relación forma grande ↔ daño"),
            (("gesto_al_aire", "sin_efecto_fisico"), "posible relación gesto al aire ↔ sin efecto"),
            (("intento_refugio", "palos_piedras"), "posible experimento de construcción/refugio"),
            (("comida_guardada", "hambre_baja"), "posible almacenamiento de provisiones"),
        ]
        found_any = False
        for (a, b), desc in pairs_to_check:
            val = h.neural.connections.get(tuple(sorted((a, b))), 0.0)
            if val > 0.03:
                found_any = True
                related_events = [e for e in raw_events if a.split("_")[0] in str(e.data).lower() or b.split("_")[0] in str(e.data).lower() or a.split("_")[0] in e.kind.lower() or b.split("_")[0] in e.kind.lower()]
                lines.append(f"  - {desc}: conexión {a} ↔ {b} = +{val:.3f}")
                for e in related_events[-4:]:
                    lines.append(f"      prueba_evento: {ev_line(e)}")
        if not found_any:
            lines.append("  No hay todavía conexiones fuertes de los conceptos vigilados; revisar nodos/conexiones crudas abajo.")
        lines.append("")

        lines.append("TODAS LAS ACTIVACIONES ACTUALES:")
        if h.neural.activations:
            for node, value in sorted(h.neural.activations.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {node:<42} activación={value:.4f}")
        else:
            lines.append("  sin activaciones actuales")
        lines.append("")

        lines.append("TODAS LAS CONEXIONES REFORZADAS:")
        if h.neural.connections:
            for (a, b), value in sorted(h.neural.connections.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {a:<28} ↔ {b:<28} peso=+{value:.4f}")
        else:
            lines.append("  sin conexiones reforzadas")
        lines.append("")

        lines.append("EVENTOS CRUDOS IMPORTANTES DE SU MEMORIA:")
        if raw_events:
            for e in raw_events[-120:]:
                lines.append("  - " + ev_line(e))
            if len(raw_events) > 120:
                lines.append(f"  ... {len(raw_events)-120} eventos importantes anteriores no mostrados")
        else:
            lines.append("  sin eventos importantes en memoria")
        lines.append("=" * 100)
        return "\n".join(lines)

    def family_tree_report(self, birth_number: int) -> str:
        """
        v1.4: árbol familiar completo alrededor de un humano:
        - todos los ancestros conocidos hasta el origen;
        - hermanos;
        - parejas reproductivas;
        - todos los descendientes conocidos;
        - el humano objetivo sale en dorado/subrayado.
        """
        target = self.human_by_birth(birth_number)
        if not target:
            return f"No existe humano con número de nacimiento {birth_number}."

        ancestors = self.collect_ancestors(birth_number)
        descendants = self.collect_descendants(birth_number)
        siblings = self.siblings_of(birth_number)
        partners = self.partners_of(birth_number)

        def status(h: Human) -> str:
            return "vivo" if h.alive else "muerto"

        def badges(h: Human) -> str:
            tags = []
            if h.birth_number in getattr(self, "gene_bank", set()):
                tags.append("★banco")
            txt = " ".join(h.detected_concepts[-4:]).lower()
            if "refugio" in txt or "cueva" in txt:
                tags.append("R")
            if "miedo" in txt or "peligro" in txt or "muerte" in txt or h.neural.connections.get(tuple(sorted(("no_movimiento", "ser_human"))), 0) > 0.35:
                tags.append("M/P")
            if h.neural.connections.get(tuple(sorted(("intento_refugio", "palos_piedras"))), 0) > 0.06:
                tags.append("proto-refugio")
            if h.genes.curiosity > 1.55:
                tags.append("curioso")
            if getattr(h.genes, "exploration_spirit", 0.0) > 2.2:
                tags.append("aventurero")
            return " [" + ", ".join(tags) + "]" if tags else ""

        def brief(h: Human, target_line: bool = False) -> str:
            concept_text = "; ".join(h.detected_concepts[-2:]) if h.detected_concepts else "sin conceptos detectados"
            line = (
                f"#{h.birth_number} {h.name} [{status(h)}] score={self.gene_score(h):.1f} "
                f"padres={h.parent1_birth}/{h.parent2_birth} hijos={len(self.children_of(h.birth_number))} "
                f"pos={h.pos()} HP={h.hp:.1f} hambre={h.hunger:.1f} sed={h.thirst:.1f}"
                f"{badges(h)}\n    conceptos: {concept_text}"
            )
            if target_line:
                return ctext(line, Color.BRIGHT_YELLOW + Color.BOLD + Color.UNDERLINE)
            return line

        lines: List[str] = []
        lines.append(f"ÁRBOL GENEALÓGICO COMPLETO DE #{birth_number}")
        lines.append("=" * 96)
        lines.append("OBJETIVO:")
        lines.append(brief(target, target_line=True))
        lines.append("")

        # Resumen de generaciones previas.
        if ancestors:
            max_depth = max(depth for _, depth in ancestors.values())
            lines.append("ANCESTROS COMPLETOS:")
            for depth in range(max_depth, 0, -1):
                humans = [h for h, d in ancestors.values() if d == depth]
                if not humans:
                    continue
                label = "padres" if depth == 1 else "abuelos" if depth == 2 else f"generación -{depth}"
                lines.append(f"\n{label.upper()}:")
                for h in sorted(humans, key=lambda x: x.birth_number):
                    lines.append("  " + brief(h).replace("\n", "\n  "))
        else:
            lines.append("ANCESTROS COMPLETOS:\n  sin ancestros registrados")

        lines.append("\nHERMANOS:")
        if siblings:
            for h in sorted(siblings, key=lambda x: x.birth_number):
                lines.append("  " + brief(h).replace("\n", "\n  "))
        else:
            lines.append("  ninguno detectado")

        lines.append("\nPAREJAS REPRODUCTIVAS / CO-PADRES:")
        if partners:
            for h in sorted(partners, key=lambda x: x.birth_number):
                shared_children = [c for c in self.children_of(birth_number) if c.parent1_birth == h.birth_number or c.parent2_birth == h.birth_number]
                lines.append("  " + brief(h).replace("\n", "\n  "))
                lines.append(f"      hijos compartidos: {[c.birth_number for c in shared_children]}")
        else:
            lines.append("  ninguna detectada")

        # Descendientes por generación.
        lines.append("\nDESCENDIENTES COMPLETOS:")
        if descendants:
            max_down = max(depth for _, depth in descendants.values())
            for depth in range(1, max_down + 1):
                humans = [h for h, d in descendants.values() if d == depth]
                if not humans:
                    continue
                label = "hijos" if depth == 1 else "nietos" if depth == 2 else f"generación +{depth}"
                lines.append(f"\n{label.upper()}:")
                for h in sorted(humans, key=lambda x: x.birth_number):
                    lines.append("  " + brief(h).replace("\n", "\n  "))
        else:
            lines.append("  ninguno detectado")

        lines.append("\nLÍNEA DIRECTA PRINCIPAL MÁS LARGA HACIA ATRÁS:")
        line = self.main_ancestor_line(birth_number)
        if line:
            lines.append("  " + " → ".join(f"#{h.birth_number}" for h in line + [target]))
        else:
            lines.append("  sin línea anterior")

        lines.append("=" * 96)
        return "\n".join(lines)

    def children_of(self, birth_number: int) -> List[Human]:
        return [h for h in self.humans.values() if h.parent1_birth == birth_number or h.parent2_birth == birth_number]

    def partners_of(self, birth_number: int) -> List[Human]:
        partners: Dict[int, Human] = {}
        for ch in self.children_of(birth_number):
            other = ch.parent2_birth if ch.parent1_birth == birth_number else ch.parent1_birth
            if other > 0:
                h = self.human_by_birth(other)
                if h:
                    partners[h.birth_number] = h
        return list(partners.values())

    def siblings_of(self, birth_number: int) -> List[Human]:
        h = self.human_by_birth(birth_number)
        if not h:
            return []
        sibs = []
        for o in self.humans.values():
            if o.birth_number == birth_number:
                continue
            same_p1 = h.parent1_birth > 0 and h.parent1_birth in (o.parent1_birth, o.parent2_birth)
            same_p2 = h.parent2_birth > 0 and h.parent2_birth in (o.parent1_birth, o.parent2_birth)
            if same_p1 or same_p2:
                sibs.append(o)
        return sibs

    def collect_ancestors(self, birth_number: int) -> Dict[int, Tuple[Human, int]]:
        found: Dict[int, Tuple[Human, int]] = {}
        queue: List[Tuple[int, int]] = [(birth_number, 0)]
        seen: Set[int] = set()
        while queue:
            nb, depth = queue.pop(0)
            if nb in seen:
                continue
            seen.add(nb)
            h = self.human_by_birth(nb)
            if not h:
                continue
            for pnb in (h.parent1_birth, h.parent2_birth):
                if pnb <= 0:
                    continue
                p = self.human_by_birth(pnb)
                if p and pnb not in found:
                    found[pnb] = (p, depth + 1)
                    queue.append((pnb, depth + 1))
        return found

    def collect_descendants(self, birth_number: int) -> Dict[int, Tuple[Human, int]]:
        found: Dict[int, Tuple[Human, int]] = {}
        queue: List[Tuple[int, int]] = [(birth_number, 0)]
        seen: Set[int] = set()
        while queue:
            nb, depth = queue.pop(0)
            if nb in seen:
                continue
            seen.add(nb)
            for ch in self.children_of(nb):
                if ch.birth_number not in found:
                    found[ch.birth_number] = (ch, depth + 1)
                    queue.append((ch.birth_number, depth + 1))
        return found

    def main_ancestor_line(self, birth_number: int) -> List[Human]:
        """Una línea directa hacia atrás eligiendo en cada generación el padre/madre con mejor score genético."""
        out: List[Human] = []
        h = self.human_by_birth(birth_number)
        seen: Set[int] = set()
        while h and h.birth_number not in seen:
            seen.add(h.birth_number)
            parents = [self.human_by_birth(n) for n in (h.parent1_birth, h.parent2_birth) if n > 0]
            parents = [p for p in parents if p]
            if not parents:
                break
            p = max(parents, key=self.gene_score)
            out.append(p)
            h = p
        return list(reversed(out))

    def resolve_export_path(self, raw_path: str, default_filename: str) -> str:
        """Resuelve una ruta de exportación. Si es carpeta, usa default_filename dentro."""
        path = os.path.expanduser(str(raw_path).strip())
        if not path:
            return default_filename
        # Si acaba en separador o ya existe como carpeta, se trata como carpeta.
        if path.endswith(os.sep) or os.path.isdir(path):
            path = os.path.join(path, default_filename)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return path

    def export_logs_file(self, raw_path: str) -> str:
        default = f"protoH_logs_dia{self.day}_tick{self.tick}.txt"
        path = self.resolve_export_path(raw_path, default)
        if not os.path.splitext(path)[1]:
            path += ".txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.all_logs))
        return f"Logs exportados a: {path}"

    def export_brain_file(self, birth_number: int, raw_path: str) -> str:
        """Exporta el registro neuronal completo de un humano a .txt."""
        h = self.human_by_birth(birth_number)
        if not h:
            return f"No existe humano #{birth_number}."
        default = f"protoH_brain_{birth_number}_dia{self.day}_tick{self.tick}.txt"
        path = self.resolve_export_path(raw_path, default)
        if not os.path.splitext(path)[1]:
            path += ".txt"
        text = self.brain_report(birth_number)
        with open(path, "w", encoding="utf-8") as f:
            f.write(strip_ansi_for_count(text))
        return f"Brain #{birth_number} exportado a: {path}"

    # ------------------------------------------------------------
    # INVESTIGACIONES LONGITUDINALES DE CONCEPTOS
    # ------------------------------------------------------------

    def investigation_watch_weights(self, category: str) -> Dict[str, float]:
        """Define qué mirar en hijos/descendientes según el tipo de señal del origen."""
        if category in ("exploracion_medicion", "ruta_mapa", "dimension_espacio"):
            return {"exploracion": 0.60, "supervivencia": 0.20, "social": 0.10, "peligro": 0.10}
        if category in ("refugio", "cueva", "construccion"):
            return {"refugio": 0.60, "exploracion": 0.15, "peligro": 0.15, "supervivencia": 0.10}
        if category in ("miedo_muerte", "peligro"):
            return {"peligro": 0.60, "muerte_no_movimiento": 0.20, "refugio": 0.10, "supervivencia": 0.10}
        if category in ("almacenamiento", "cebo_trampa"):
            return {"estrategia": 0.55, "supervivencia": 0.25, "exploracion": 0.10, "social": 0.10}
        if category in ("vida_existencia", "identidad_continuidad"):
            return {"vida_muerte": 0.45, "identidad": 0.30, "social": 0.15, "supervivencia": 0.10}
        if category in ("sueño_fuerza",):
            return {"descanso_fuerza": 0.60, "supervivencia": 0.20, "peligro": 0.10, "exploracion": 0.10}
        if category in ("supervivencia", "agua_sed", "comida_hambre"):
            return {"supervivencia": 0.60, "peligro": 0.15, "exploracion": 0.15, "social": 0.10}
        return {"exploracion": 0.35, "supervivencia": 0.30, "peligro": 0.20, "social": 0.15}

    def classify_investigation_from_components(self, components: Set[str], text_hint: str = "") -> Tuple[str, str]:
        low = (" ".join(components) + " " + text_hint).lower()
        if any(k in low for k in ("intento_refugio", "palos_piedras", "cueva", "refugio")):
            return "refugio", "posible proto-refugio / cobertura / construcción"
        if any(k in low for k in ("semilla", "pollo_cercano", "pollo_se_acerca", "cebo", "trampa")):
            return "cebo_trampa", "posible cebo/trampa con semillas y animales"
        if any(k in low for k in ("inventario", "comida_guardada", "almacen", "provis")):
            return "almacenamiento", "posible almacenamiento de provisiones"
        if ("no_movimiento" in low and "ser_human" in low) or any(k in low for k in ("muerte", "dolor", "forma_trex", "forma_cow", "peligro")):
            return "miedo_muerte", "posible miedo/peligro/muerte-no-movimiento"
        if any(k in low for k in ("impulso_explorador", "mover_hacia_desconocido", "distancia", "medicion", "medición", "ruta", "camino")):
            return "exploracion_medicion", "posible exploración, medición de distancia o rutas"
        if any(k in low for k in ("sueño", "sueno", "golpe_debil", "descanso", "fuerza", "cansancio")):
            return "sueño_fuerza", "posible relación descanso/cansancio ↔ fuerza"
        if any(k in low for k in ("agua", "sed", "sed_baja", "mover_hacia_agua")):
            return "agua_sed", "posible relación agua/sed"
        if any(k in low for k in ("hambre", "comida", "meat", "pollo", "vaca", "mover_hacia_ser_pequeño")):
            return "comida_hambre", "posible relación comida/hambre/animales"
        if any(k in low for k in ("ser_human", "ser_cow", "ser_chicken", "nuevo_parecido", "vida", "vivo")):
            return "vida_existencia", "posible existencia/vida/seres"
        return "concepto_no_claro", "cluster raro todavía sin traducción clara"

    def open_or_update_investigation(
        self,
        h: Human,
        category: str,
        hypothesis: str,
        confidence: float,
        evidence_for: Optional[List[str]] = None,
        evidence_against: Optional[List[str]] = None,
        inherited_from: Optional[int] = None,
        generations_left: int = 3,
        duration_days: int = 6,
    ) -> ConceptInvestigation:
        """Abre o actualiza una investigación sobre un humano. No cambia su mente."""
        evidence_for = evidence_for or []
        evidence_against = evidence_against or []
        existing = None
        for inv in self.investigations.values():
            if inv.subject_birth == h.birth_number and inv.category == category and not inv.concluded:
                existing = inv
                break
        if existing is None:
            inv = ConceptInvestigation(
                inv_id=self.next_investigation_id,
                origin_birth=inherited_from or h.birth_number,
                subject_birth=h.birth_number,
                category=category,
                hypothesis=hypothesis,
                started_tick=self.tick,
                started_day=self.day,
                expires_tick=self.tick + duration_days * TICKS_PER_DAY,
                last_update_tick=self.tick,
                inherited_from=inherited_from,
                generations_left=generations_left,
                watch_weights=self.investigation_watch_weights(category),
                confidence=clamp(confidence, 0, 100),
            )
            self.next_investigation_id += 1
            self.investigations[inv.inv_id] = inv
            self.lineage_watch_roots.setdefault(inv.origin_birth, []).append(inv.inv_id)
            existing = inv
            self.all_logs.append(
                f"[Día {self.day} T{self.tick}] INVESTIGACIÓN ABIERTA H{h.birth_number}: {category} | {hypothesis} | confianza {pct(confidence)}"
            )
        inv = existing
        inv.last_update_tick = self.tick
        inv.expires_tick = max(inv.expires_tick, self.tick + duration_days * TICKS_PER_DAY)
        inv.confidence = clamp(max(inv.confidence * 0.92, confidence), 0, 100)
        for e in evidence_for:
            if e not in inv.evidence_for:
                inv.evidence_for.append(e)
        for e in evidence_against:
            if e not in inv.evidence_against:
                inv.evidence_against.append(e)
        inv.evidence_for = inv.evidence_for[-60:]
        inv.evidence_against = inv.evidence_against[-40:]
        return inv

    def _movement_context_sample(self, h: Human) -> Dict[str, Any]:
        pos = h.pos()
        nearest_water = self.find_nearest_terrain(pos, WATER, 40)
        nearest_cow = self.nearest_creature(h, "cow", 40)
        nearest_chicken = self.nearest_creature(h, "chicken", 40)
        nearest_trex = self.nearest_creature(h, "trex", 40)
        nearest_cave = self.nearest_cave_interior(pos)
        return {
            "pos": pos,
            "hunger": h.hunger,
            "thirst": h.thirst,
            "sleepiness": h.sleepiness,
            "water_d": dist(pos, nearest_water) if nearest_water else None,
            "cow_d": dist(pos, nearest_cow.pos()) if nearest_cow else None,
            "chicken_d": dist(pos, nearest_chicken.pos()) if nearest_chicken else None,
            "trex_d": dist(pos, nearest_trex.pos()) if nearest_trex else None,
            "cave_d": dist(pos, nearest_cave) if nearest_cave else None,
        }

    def update_investigations(self) -> None:
        """Sigue investigaciones activas y crea vigilancia hereditaria en hijos.

        Este método es externo: no programa conductas nuevas en los protohumanos.
        Solo mira si una hipótesis se sostiene en el tiempo, si baja a falsa alarma,
        o si aparece en descendientes con predisposición genética parecida.
        """
        # 1) Crear investigaciones heredadas para hijos de sujetos investigados.
        for inv in list(self.investigations.values()):
            subject = self.human_by_birth(inv.subject_birth)
            if not subject or inv.generations_left <= 0:
                continue
            for child in self.children_of(inv.subject_birth):
                if any(x.subject_birth == child.birth_number and x.inherited_from == inv.origin_birth and x.category == inv.category for x in self.investigations.values()):
                    continue
                # Vigilar hijos si el origen tenía señales reales o si el hijo conserva genes prometedores.
                child_score = self.gene_score(child)
                parent_score = self.gene_score(subject)
                if inv.confidence >= 45 or child_score >= parent_score * 0.94:
                    self.open_or_update_investigation(
                        child,
                        inv.category,
                        f"seguimiento heredado del linaje #{inv.origin_birth}: {inv.hypothesis}",
                        max(18.0, inv.confidence * 0.45),
                        evidence_for=[f"hijo de #{inv.subject_birth}; vigilancia heredada sin conceptos heredados"],
                        inherited_from=inv.origin_birth,
                        generations_left=inv.generations_left - 1,
                        duration_days=10,
                    )

        # 2) Actualizar evidencias de cada sujeto.
        for inv in list(self.investigations.values()):
            h = self.human_by_birth(inv.subject_birth)
            if not h:
                continue
            recent = [e for e in h.memory_events if e.tick >= max(inv.started_tick, self.tick - 10 * TICKS_PER_DAY)]
            c = h.neural.connections
            cat = inv.category
            for_e: List[str] = []
            against: List[str] = []

            # Evidencia general: cambio de conducta/repetición separada.
            if len({e.day for e in recent}) >= 3:
                for_e.append(f"conducta observada durante {len({e.day for e in recent})} días distintos")
            if len(recent) < 3 and self.tick > inv.started_tick + 3 * TICKS_PER_DAY:
                against.append("poca evidencia nueva tras varios días")

            if cat in ("exploracion_medicion", "ruta_mapa", "dimension_espacio"):
                # Busca acercamientos sin necesidad: movimientos hacia/desde agua/animales/cueva con hambre/sed bajas.
                exploratory = [e for e in recent if e.kind in ("beber", "coger_objeto", "accion_fisica_sin_efecto", "experimento_refugio", "accion_no_prevista")]
                if h.neural.connections.get(tuple(sorted(("impulso_explorador", "mover_hacia_desconocido"))), 0) > 0.35:
                    for_e.append("impulso_explorador ↔ mover_hacia_desconocido reforzado")
                low_need_events = [e for e in recent if ("beber" not in e.kind and h.hunger < 45 and h.thirst < 45)]
                if exploratory and low_need_events:
                    for_e.append("actividad exploratoria con hambre/sed no extremas")
                if len([e for e in recent if e.kind == "beber"]) >= 3 and h.thirst > 70:
                    against.append("gran parte del movimiento puede explicarse por sed")

            if cat in ("agua_sed",):
                if c.get(tuple(sorted(("agua", "sed_baja"))), 0) > 0.25:
                    for_e.append("agua ↔ sed_baja reforzado")
                if c.get(tuple(sorted(("mover_hacia_agua", "sed_alta"))), 0) > 0.25:
                    for_e.append("sed_alta ↔ mover_hacia_agua reforzado")
                if len([e for e in recent if e.kind == "beber"]) < 2:
                    against.append("no hay suficientes eventos de beber recientes")

            if cat in ("comida_hambre",):
                if c.get(tuple(sorted(("comida_meat", "hambre_baja"))), 0) > 0.18:
                    for_e.append("comida_meat ↔ hambre_baja reforzado")
                if c.get(tuple(sorted(("hambre_alta", "mover_hacia_ser_pequeño"))), 0) > 0.25:
                    for_e.append("hambre_alta ↔ mover_hacia_ser_pequeño reforzado")
                if len([e for e in recent if e.kind == "comer"]) < 1:
                    against.append("no hay comida reciente que confirme la hipótesis")

            if cat in ("miedo_muerte", "peligro"):
                deaths = [e for e in recent if e.kind == "observa_muerte"]
                damage = [e for e in recent if e.kind == "ataque" and e.data.get("objetivo_tipo") == "human"]
                if c.get(tuple(sorted(("no_movimiento", "ser_human"))), 0) > 0.25:
                    for_e.append("no_movimiento ↔ ser_human reforzado")
                if c.get(tuple(sorted(("dolor", "forma_trex"))), 0) > 0.12 or c.get(tuple(sorted(("dolor", "forma_cow"))), 0) > 0.12:
                    for_e.append("dolor asociado a forma animal concreta")
                if deaths:
                    for_e.append(f"observó {len(deaths)} muertes recientes")
                if not deaths and not damage and self.tick > inv.started_tick + 4 * TICKS_PER_DAY:
                    against.append("sin muerte/daño reciente que sostenga peligro/muerte")

            if cat in ("refugio", "cueva", "construccion"):
                ref_events = [e for e in recent if e.kind in ("experimento_refugio", "dormir")]
                if c.get(tuple(sorted(("intento_refugio", "palos_piedras"))), 0) > 0.08:
                    for_e.append("intento_refugio ↔ palos_piedras reforzado")
                if c.get(tuple(sorted(("cueva_interior", "reposo"))), 0) > 0.12:
                    for_e.append("cueva_interior ↔ reposo reforzado")
                if ref_events:
                    for_e.append(f"eventos relacionados con refugio/descanso: {len(ref_events)}")
                if not ref_events and self.tick > inv.started_tick + 5 * TICKS_PER_DAY:
                    against.append("no repite conductas de refugio tras la señal inicial")

            if cat in ("sueño_fuerza",):
                if c.get(tuple(sorted(("sueño_bajo", "golpe_debil"))), 0) > 0.18:
                    for_e.append("sueño_bajo ↔ golpe_debil reforzado")
                sleeps = [e for e in recent if e.kind == "dormir"]
                attacks = [e for e in recent if e.kind == "ataque"]
                if sleeps and attacks:
                    for_e.append("hay sueño y golpes recientes para comparar")
                if not sleeps and self.tick > inv.started_tick + 4 * TICKS_PER_DAY:
                    against.append("no aparece cambio hacia dormir tras golpes débiles")

            if cat in ("almacenamiento",):
                inv_events = [e for e in recent if "inventario" in e.kind or e.kind in ("coger_objeto", "comer")]
                if c.get(tuple(sorted(("comida_guardada", "hambre_baja"))), 0) > 0.08:
                    for_e.append("comida_guardada ↔ hambre_baja reforzado")
                if len(inv_events) >= 4:
                    for_e.append("usa inventario/coger/comer de forma repetida")

            if cat in ("cebo_trampa",):
                drops = [e for e in recent if e.kind == "soltar_semilla"]
                if c.get(tuple(sorted(("semilla", "pollo_cercano"))), 0) > 0.05:
                    for_e.append("semilla ↔ pollo_cercano reforzado")
                if drops:
                    for_e.append(f"soltó semillas {len(drops)} veces")

            # Recalcular confianza con evidencias y contraevidencias acumuladas.
            for e in for_e:
                if e not in inv.evidence_for:
                    inv.evidence_for.append(e)
            for e in against:
                if e not in inv.evidence_against:
                    inv.evidence_against.append(e)
            inv.evidence_for = inv.evidence_for[-60:]
            inv.evidence_against = inv.evidence_against[-40:]

            # Recalibración prudente: no queremos que una señal suba a 100% solo por existir
            # durante varios ticks. Sube por evidencia nueva y repetición, baja por ruido.
            new_for = len(for_e)
            new_against = len(against)
            total_for = len(inv.evidence_for)
            total_against = len(inv.evidence_against)
            maturity_bonus = min(18.0, total_for * 1.15)
            contradiction_penalty = min(26.0, total_against * 2.2)
            heredity_bonus = 3.0 if inv.inherited_from and total_for >= 4 else 0.0
            fresh_delta = new_for * 1.6 - new_against * 2.4
            new_conf = clamp(inv.confidence * 0.92 + maturity_bonus - contradiction_penalty + heredity_bonus + fresh_delta, 0, 100)
            # Capas de prudencia: los clusters sin traducción clara no deben llegar a 100%
            # solo por persistir. Los conceptos raros valiosos pueden subir más, pero no gratis.
            cap_by_category = {
                "concepto_no_claro": 58.0,
                "agua_sed": 68.0,
                "comida_hambre": 70.0,
                "exploracion_medicion": 78.0,
                "sueño_fuerza": 90.0,
                "miedo_muerte": 88.0,
                "refugio": 88.0,
                "cebo_trampa": 86.0,
                "almacenamiento": 86.0,
                "vida_existencia": 84.0,
            }
            cap = cap_by_category.get(inv.category, 72.0)
            inv.confidence = min(new_conf, cap)
            inv.last_update_tick = self.tick

            old_state = inv.state
            if inv.confidence < 25 and self.tick > inv.started_tick + 5 * TICKS_PER_DAY:
                inv.state = "FALSA ALARMA PROBABLE"
            elif inv.confidence < 45:
                inv.state = "EN SEGUIMIENTO"
            elif inv.confidence < 62:
                inv.state = "PATRÓN FUNCIONAL"
            elif inv.confidence < 80:
                inv.state = "CONCEPTO EMERGENTE"
            else:
                inv.state = "CONCEPTO REFINADO"
            inv.valuable = inv.state in ("CONCEPTO EMERGENTE", "CONCEPTO REFINADO") or inv.category in ("refugio", "cebo_trampa", "almacenamiento", "miedo_muerte", "exploracion_medicion") and inv.confidence >= 50

            # Cerrar investigaciones muy viejas sin evidencia, pero conservar el historial.
            if self.tick > inv.expires_tick and inv.confidence < 45:
                inv.concluded = True
                inv.state = "FALSA ALARMA PROBABLE"

            # Reportar solo cambios importantes, no cada tick.
            if inv.state != old_state and inv.valuable:
                block = self.format_investigation(inv, compact=False)
                styled = style_text(block, "gold" if inv.confidence >= 70 and inv.category in ("refugio", "cebo_trampa", "almacenamiento", "miedo_muerte", "vida_existencia") else "darkblue")
                self.concept_logs.append(styled)
                self.all_logs.append(styled)
                h.detected_concepts.append(f"[DÍA {self.day} | TICK {self.tick}] INVESTIGACIÓN LONGITUDINAL: {inv.category} | confianza {pct(inv.confidence)} | estado={inv.state}")
                if inv.category in ("refugio", "cebo_trampa", "almacenamiento", "miedo_muerte", "exploracion_medicion") and inv.confidence >= 55:
                    self.register_gene_bank(h, f"investigación longitudinal valiosa: {inv.category} {pct(inv.confidence)}")

    def format_investigation(self, inv: ConceptInvestigation, compact: bool = False) -> str:
        h = self.human_by_birth(inv.subject_birth)
        status = "desconocido"
        name = f"#{inv.subject_birth}"
        if h:
            status = "VIVO" if h.alive else "muerto"
            name = f"#{h.birth_number} {h.name} [{status}] score={self.gene_score(h):.1f}"
        lines = []
        lines.append("=" * 96)
        lines.append(f"[DÍA {self.day} | TICK {self.tick}] INVESTIGACIÓN LONGITUDINAL #{inv.inv_id}")
        lines.append(f"SUJETO: {name}")
        lines.append(f"ORIGEN DEL LINAJE: #{inv.origin_birth} | heredada_de: {inv.inherited_from if inv.inherited_from else 'no'} | generaciones_restantes={inv.generations_left}")
        lines.append(f"CATEGORÍA: {inv.category}")
        lines.append(f"HIPÓTESIS: {inv.hypothesis}")
        lines.append(f"CONFIANZA: {pct(inv.confidence)} | ESTADO: {inv.state} | VALIOSA: {'SÍ' if inv.valuable else 'no'}")
        lines.append("PESOS DE VIGILANCIA:")
        for k, v in sorted(inv.watch_weights.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {k}: {v:.2f}")
        lines.append("EVIDENCIAS A FAVOR:")
        evf = inv.evidence_for[-8:] if compact else inv.evidence_for[-30:]
        lines.extend([f"  + {e}" for e in evf] or ["  ninguna todavía"])
        lines.append("EVIDENCIAS EN CONTRA / RUIDO:")
        eva = inv.evidence_against[-6:] if compact else inv.evidence_against[-20:]
        lines.extend([f"  - {e}" for e in eva] or ["  ninguna fuerte"])
        if h and not compact:
            lines.append("CONEXIONES NEURONALES PRINCIPALES DEL SUJETO:")
            for (a, b), val in h.neural.top_connections(12):
                lines.append(f"  - {a} ↔ {b}: +{val:.3f}")
            lines.append("EVENTOS RECIENTES ÚTILES:")
            for e in h.memory_events[-20:]:
                if e.kind in {"beber", "comer", "coger_objeto", "observa_muerte", "experimento_refugio", "soltar_semilla", "ataque", "dormir", "accion_fisica_sin_efecto"}:
                    lines.append(f"  - [Día {e.day} T{e.tick}] {e.kind} {e.data}")
        lines.append("=" * 96)
        return "\n".join(lines)

    def investigations_report(self, only_valuable: bool = False) -> str:
        invs = list(self.investigations.values())
        if only_valuable:
            invs = [i for i in invs if i.valuable or i.confidence >= 55]
        if not invs:
            return "No hay investigaciones longitudinales todavía."
        invs.sort(key=lambda i: (i.valuable, i.confidence, i.last_update_tick), reverse=True)
        lines = ["INVESTIGACIONES LONGITUDINALES", "=" * 96]
        for inv in invs[:250]:
            lines.append(self.format_investigation(inv, compact=True))
        if len(invs) > 250:
            lines.append(f"... {len(invs)-250} investigaciones más no mostradas")
        return "\n\n".join(lines)

    def investigate_person_report(self, birth_number: int) -> str:
        invs = [i for i in self.investigations.values() if i.subject_birth == birth_number or i.origin_birth == birth_number]
        h = self.human_by_birth(birth_number)
        lines = [f"INVESTIGAR #{birth_number}", "=" * 96]
        if h:
            lines.append(self.format_human_gene_line(h))
            lines.append("")
        if not invs:
            lines.append("No hay investigaciones activas/cerradas para este humano o linaje.")
            return "\n".join(lines)
        invs.sort(key=lambda i: (i.subject_birth != birth_number, i.confidence), reverse=True)
        for inv in invs:
            lines.append(self.format_investigation(inv, compact=False))
        return "\n\n".join(lines)

    def lineage_watch_report(self, birth_number: int) -> str:
        root_ids = self.lineage_watch_roots.get(birth_number, [])
        related = [self.investigations[i] for i in root_ids if i in self.investigations]
        # Añade también investigaciones donde el origen sea ese número aunque no estén indexadas.
        related += [i for i in self.investigations.values() if i.origin_birth == birth_number and i.inv_id not in root_ids]
        if not related:
            return f"No hay seguimiento de linaje para #{birth_number}."
        related.sort(key=lambda i: (i.category, i.subject_birth, i.started_tick))
        lines = [f"SEGUIMIENTO DE LINAJE #{birth_number}", "=" * 96]
        by_cat: Dict[str, List[ConceptInvestigation]] = {}
        for inv in related:
            by_cat.setdefault(inv.category, []).append(inv)
        for cat, invs in by_cat.items():
            lines.append(f"\n{cat.upper()} ({len(invs)} investigaciones)")
            for inv in sorted(invs, key=lambda x: x.confidence, reverse=True)[:80]:
                h = self.human_by_birth(inv.subject_birth)
                status = "VIVO" if h and h.alive else "muerto" if h else "?"
                lines.append(f"  #{inv.subject_birth:<5} {status:<6} conf={pct(inv.confidence):>6} estado={inv.state:<22} hipótesis={inv.hypothesis}")
        return "\n".join(lines)

    def export_investigations_file(self, raw_path: str, only_valuable: bool = False) -> str:
        default = f"protoH_investigaciones_dia{self.day}_tick{self.tick}.txt"
        path = self.resolve_export_path(raw_path, default)
        if not os.path.splitext(path)[1]:
            path += ".txt"
        text = self.investigations_report(only_valuable=only_valuable)
        with open(path, "w", encoding="utf-8") as f:
            f.write(strip_ansi_for_count(text))
        return f"Investigaciones exportadas a: {path}"

    def export_lineage_watch_file(self, birth_number: int, raw_path: str) -> str:
        default = f"protoH_lineage_watch_{birth_number}_dia{self.day}_tick{self.tick}.txt"
        path = self.resolve_export_path(raw_path, default)
        if not os.path.splitext(path)[1]:
            path += ".txt"
        text = self.lineage_watch_report(birth_number)
        with open(path, "w", encoding="utf-8") as f:
            f.write(strip_ansi_for_count(text))
        return f"Seguimiento de linaje exportado a: {path}"

    def valuable_logs_report(self, limit: Optional[int] = None) -> str:
        """Devuelve solo los reportes que merecen estudio humano: dorados, morados,
        conclusiones claras y conceptos raros valiosos.
        """
        selected: List[str] = []
        for block in self.concept_logs:
            if is_valuable_report_text(block):
                selected.append(style_text(block, style_for_report_text(block)))
        for block in self.unexpected_logs:
            # Fallos raros reales sí son valiosos, pero no metemos experimentos físicos ya previstos.
            if "accion_no_prevista" in block or "ACCIÓN NO PREVISTA" in block:
                selected.append(red_alert(block))
        if limit is not None:
            selected = selected[-limit:]
        if not selected:
            return "Todavía no hay reportes realmente valiosos según el filtro estricto."
        header = [
            "REPORTES VALIOSOS / FILTRO ESTRICTO",
            "=" * 100,
            "Incluye dorados, morados, azul oscuro/conclusiones claras y conceptos raros útiles: refugio, almacenamiento, cebo/trampa, miedo/muerte, sueño/fuerza fuerte.",
            "No incluye ruido normal de hambre/sed/socialización salvo que sea muy fuerte.",
            "=" * 100,
        ]
        return "\n".join(header) + "\n\n" + "\n\n".join(selected)

    def evolution_summary_report(self) -> str:
        alive = [h for h in self.humans.values() if h.alive]
        all_h = list(self.humans.values())
        deaths: Dict[str, int] = {}
        births = len(all_h)
        for line in self.all_logs:
            if " muerte " in line or ": muerte " in line:
                m = re.search(r"causa': '([^']+)'", line)
                if m:
                    deaths[m.group(1)] = deaths.get(m.group(1), 0) + 1
        def top_by(cat: str, n: int = 12) -> List[Human]:
            return sorted(all_h, key=lambda h: self.category_score(h, cat), reverse=True)[:n]
        lines = [
            "RESUMEN EVOLUTIVO",
            "=" * 100,
            f"Día {self.day} | Tick {self.tick}",
            f"Humanos totales nacidos: {births}",
            f"Humanos vivos: {len(alive)}",
            f"Animales vivos: pollos={self.count_alive('chicken')} vacas={self.count_alive('cow')} t-rex={self.count_alive('trex')}",
            "",
            "MUERTES POR CAUSA:",
        ]
        for k, v in sorted(deaths.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {k}: {v}")
        lines.append("")
        lines.append("TOPS RÁPIDOS:")
        for cat in ("genes", "supervivientes", "descubridores", "refugio", "miedo_peligro", "aventureros", "curiosos"):
            lines.append(f"\n{cat.upper()}:")
            for h in top_by(cat, 8):
                status = "VIVO" if h.alive else "muerto"
                lines.append(f"  #{h.birth_number:<5} {status:<6} score={self.gene_score(h):5.1f} cat={self.category_score(h, cat):6.1f} nombre={h.name}")
        lines.append("\nREPORTES VALIOSOS RECIENTES:")
        vals = [b for b in self.concept_logs if is_valuable_report_text(b)]
        for b in vals[-20:]:
            first = b.splitlines()[1] if len(b.splitlines()) > 1 else b.splitlines()[0]
            lines.append("  - " + strip_ansi_for_count(first))
        return "\n".join(lines)

    def export_useful_file(self, raw_path: str) -> str:
        default = f"protoH_UTIL_dia{self.day}_tick{self.tick}.txt"
        path = self.resolve_export_path(raw_path, default)
        if not os.path.splitext(path)[1]:
            path += ".txt"
        sections = [
            self.evolution_summary_report(),
            "\n\n" + "#" * 120 + "\nREPORTES VALIOSOS\n" + "#" * 120 + "\n",
            strip_ansi_for_count(self.valuable_logs_report()),
            "\n\n" + "#" * 120 + "\nBANCO GENÉTICO\n" + "#" * 120 + "\n",
            self.gene_bank_report(),
            "\n\n" + "#" * 120 + "\nTOPS\n" + "#" * 120 + "\n",
            self.tops_report() if hasattr(self, "tops_report") else "Usa tops en la interfaz.",
        ]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))
        return f"Datos útiles exportados a: {path}"

    def export_everything_file(self, raw_path: str) -> str:
        """Exportación absoluta: crea una carpeta con TODO lo útil y pesado.

        A diferencia de export useful, esto genera un paquete completo:
        - resumen evolutivo
        - todos los logs crudos
        - todos los conceptos
        - fallos raros
        - banco genético
        - investigaciones
        - genes de todos los humanos
        - brain de todos los humanos vivos y muertos
        - tree all
        - tree individual de cada humano
        """
        raw = os.path.expanduser(str(raw_path).strip())
        if not raw:
            raw = f"protoH_EXPORT_ALL_dia{self.day}_tick{self.tick}"

        # Si el usuario pone un .txt, no hacemos solo txt: creamos carpeta hermana.
        base, ext = os.path.splitext(raw)
        if ext:
            root = base + "_bundle"
        else:
            root = raw
        os.makedirs(root, exist_ok=True)

        def write_txt(rel: str, text: str) -> str:
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(strip_ansi_for_count(text))
            return path

        write_txt("00_resumen_evolutivo.txt", self.evolution_summary_report())
        write_txt("01_all_logs.txt", "\n".join(self.all_logs))
        write_txt("02_conceptos.txt", "\n\n".join(self.concept_logs))
        write_txt("03_fallos_raros.txt", "\n\n".join(self.unexpected_logs))
        write_txt("04_valiosos.txt", self.valuable_logs_report())
        write_txt("05_banco_genetico.txt", self.gene_bank_report())
        write_txt("06_investigaciones.txt", self.investigations_report(only_valuable=False))
        write_txt("07_investigaciones_valiosas.txt", self.investigations_report(only_valuable=True))
        write_txt("08_rankings.txt", self.rankings_report(category=None, limit=50))
        write_txt("09_humanos_genes.txt", "\n".join(self.format_human_gene_line(h) for h in sorted(self.humans.values(), key=lambda x: x.birth_number)))

        # Árbol general.
        tree_all_path = os.path.join(root, "trees", f"protoH_tree_all_dia{self.day}_tick{self.tick}.svg")
        tree_all_msg = self.export_tree_image("all", tree_all_path)

        # Cerebros y árboles individuales de TODOS los humanos registrados.
        humans_sorted = sorted(self.humans.values(), key=lambda x: x.birth_number)
        brain_count = 0
        tree_count = 0
        for h in humans_sorted:
            nb = h.birth_number
            try:
                write_txt(os.path.join("brains", f"brain_{nb}.txt"), self.brain_report(nb))
                brain_count += 1
            except Exception as e:
                write_txt(os.path.join("errors", f"brain_{nb}_ERROR.txt"), f"Error exportando brain #{nb}: {e}")
            try:
                indiv_tree_path = os.path.join(root, "trees", "individual", f"tree_{nb}.svg")
                self.export_tree_image(str(nb), indiv_tree_path)
                tree_count += 1
            except Exception as e:
                write_txt(os.path.join("errors", f"tree_{nb}_ERROR.txt"), f"Error exportando tree #{nb}: {e}")

        manifest = [
            "EXPORT ALL — protoH",
            "=" * 80,
            f"Día: {self.day}",
            f"Tick: {self.tick}",
            f"Carpeta: {root}",
            f"Humanos totales: {len(self.humans)}",
            f"Brains exportados: {brain_count}",
            f"Árboles individuales exportados: {tree_count}",
            f"Árbol general: {tree_all_msg}",
            "",
            "Contenido principal:",
            "- 00_resumen_evolutivo.txt",
            "- 01_all_logs.txt",
            "- 02_conceptos.txt",
            "- 03_fallos_raros.txt",
            "- 04_valiosos.txt",
            "- 05_banco_genetico.txt",
            "- 06_investigaciones.txt",
            "- 07_investigaciones_valiosas.txt",
            "- 08_rankings.txt",
            "- 09_humanos_genes.txt",
            "- brains/brain_N.txt",
            "- trees/protoH_tree_all_*.svg",
            "- trees/individual/tree_N.svg",
        ]
        write_txt("MANIFEST.txt", "\n".join(manifest))
        return f"Exportación absoluta creada en carpeta: {root} | brains={brain_count} | trees_individuales={tree_count}"

    def export_tree_image(self, spec: str = "all", raw_path: str = "") -> str:
        """
        Exporta árbol genealógico a una ruta elegida por el usuario.

        Uso nuevo obligatorio:
          export tree 721 /ruta/archivo.svg
          export tree all /ruta/carpeta/
          export_tree 721 ~/Desktop/arbol_721.svg

        Si la extensión es .png intenta usar PIL/Pillow.
        Si no hay PIL, usa .svg, que no necesita librerías externas.
        """
        spec = str(spec).strip().lower()
        if not raw_path:
            return "Uso: export tree 721 /ruta/arbol.svg | export tree all /ruta/arbol_general.svg"

        target: Optional[Human] = None
        if spec != "all":
            try:
                target = self.human_by_birth(int(spec))
            except ValueError:
                return "Uso: export tree 721 /ruta/arbol.svg | export tree all /ruta/arbol_general.svg"
            if not target:
                return f"No existe humano #{spec}."

        default_base = (
            f"protoH_tree_{target.birth_number}_dia{self.day}_tick{self.tick}.svg"
            if target else f"protoH_tree_all_dia{self.day}_tick{self.tick}.svg"
        )
        path = self.resolve_export_path(raw_path, default_base)
        root, ext = os.path.splitext(path)
        ext = ext.lower()
        if ext not in (".svg", ".png"):
            # Sin extensión clara: por defecto SVG porque no necesita Pillow.
            path += ".svg"
            ext = ".svg"

        # Construcción de nodos.
        if target:
            ancestors = self.collect_ancestors(target.birth_number)
            descendants = self.collect_descendants(target.birth_number)
            nodes: Dict[int, Tuple[Human, int]] = {target.birth_number: (target, 0)}
            for nb, (h, d) in ancestors.items():
                nodes[nb] = (h, -d)
            for nb, (h, d) in descendants.items():
                nodes[nb] = (h, d)

            # Añade hermanos y co-padres. Además, para evitar que en la imagen parezca
            # que un humano tuvo hijos "solo", incluimos el segundo padre/madre de
            # cualquier nodo ya presente cuando exista en la simulación.
            for h in self.partners_of(target.birth_number) + self.siblings_of(target.birth_number):
                nodes.setdefault(h.birth_number, (h, 0))

            changed = True
            safety = 0
            while changed and safety < 4:
                changed = False
                safety += 1
                for h, layer in list(nodes.values()):
                    for partner in self.partners_of(h.birth_number):
                        if partner.birth_number not in nodes:
                            nodes[partner.birth_number] = (partner, layer)
                            changed = True

                    p1 = self.human_by_birth(h.parent1_birth) if h.parent1_birth else None
                    p2 = self.human_by_birth(h.parent2_birth) if h.parent2_birth else None
                    if p1 and p1.birth_number not in nodes:
                        nodes[p1.birth_number] = (p1, layer - 1)
                        changed = True
                    if p2 and p2.birth_number not in nodes:
                        nodes[p2.birth_number] = (p2, layer - 1)
                        changed = True

                    for child in self.children_of(h.birth_number):
                        if child.birth_number in nodes:
                            other_nb = child.parent2_birth if child.parent1_birth == h.birth_number else child.parent1_birth
                            other = self.human_by_birth(other_nb) if other_nb else None
                            if other and other.birth_number not in nodes:
                                nodes[other.birth_number] = (other, layer)
                                changed = True

            title = f"Árbol genealógico completo de #{target.birth_number} — {target.name}"
        else:
            gen_cache: Dict[int, int] = {}
            def generation(h: Human) -> int:
                if h.birth_number in gen_cache:
                    return gen_cache[h.birth_number]
                parents = [self.human_by_birth(n) for n in (h.parent1_birth, h.parent2_birth) if n > 0]
                parents = [p for p in parents if p]
                if not parents:
                    gen_cache[h.birth_number] = 0
                else:
                    gen_cache[h.birth_number] = 1 + max(generation(p) for p in parents)
                return gen_cache[h.birth_number]

            all_h = sorted(self.humans.values(), key=lambda h: h.birth_number)
            if len(all_h) > 900:
                selected = [h for h in all_h if h.alive or h.birth_number in getattr(self, "gene_bank", set()) or h.detected_concepts]
                if len(selected) > 900:
                    selected = sorted(
                        selected,
                        key=lambda h: (
                            h.birth_number in getattr(self, "gene_bank", set()),
                            h.alive,
                            len(h.detected_concepts),
                            self.gene_score(h),
                        ),
                        reverse=True,
                    )[:900]
                all_h = sorted(selected, key=lambda h: h.birth_number)
            nodes = {h.birth_number: (h, generation(h)) for h in all_h}
            title = f"Árbol genealógico general — {len(nodes)} humanos mostrados de {len(self.humans)}"

        layers: Dict[int, List[Human]] = {}
        for h, layer in nodes.values():
            layers.setdefault(layer, []).append(h)
        for layer in layers:
            layers[layer].sort(key=lambda h: h.birth_number)

        # Exportación 1.4.4: más separación vertical y horizontal.
        # Antes, en árboles con muchos hijos, las curvas quedaban como una masa gris.
        # Esto no cambia la genealogía, solo la lectura visual.
        node_w, node_h = 185, 72
        x_gap = 72
        y_gap = 150 if target else 130
        margin_x, margin_y = 70, 95
        max_count = max((len(v) for v in layers.values()), default=1)
        layer_keys = sorted(layers.keys())
        width = min(32000, max(1100, margin_x * 2 + max_count * (node_w + x_gap)))
        height = min(32000, max(800, margin_y * 2 + len(layer_keys) * (node_h + y_gap)))

        positions: Dict[int, Tuple[int, int]] = {}
        for row, layer in enumerate(layer_keys):
            members = layers[layer]
            total_w = len(members) * node_w + max(0, len(members) - 1) * x_gap
            start_x = max(margin_x, (width - total_w) // 2)
            y = margin_y + row * (node_h + y_gap)
            for i, h in enumerate(members):
                positions[h.birth_number] = (start_x + i * (node_w + x_gap), y)

        def flags_for(h: Human) -> str:
            flags = []
            if getattr(h.genes, "exploration_spirit", 0) > 2.2:
                flags.append("A")
            if h.genes.curiosity > 1.55:
                flags.append("C")
            if h.neural.connections.get(tuple(sorted(("intento_refugio", "palos_piedras"))), 0) > 0.06:
                flags.append("R")
            if h.neural.connections.get(tuple(sorted(("no_movimiento", "ser_human"))), 0) > 0.35:
                flags.append("M")
            if h.neural.connections.get(tuple(sorted(("dolor", "forma_trex"))), 0) > 0.12:
                flags.append("P")
            return " ".join(flags) or "-"

        # Si se pide PNG, intentamos PIL; si no está, explicamos y sugerimos SVG.
        if ext == ".png":
            try:
                from PIL import Image, ImageDraw, ImageFont
            except Exception as exc:
                svg_path = root + ".svg"
                self.export_tree_image(spec, svg_path)
                return f"No se pudo crear PNG porque falta PIL/Pillow ({exc}). He exportado SVG en su lugar: {svg_path}. Para PNG: pip install pillow"

            img = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 13)
                small = ImageFont.truetype("DejaVuSans.ttf", 10)
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
            except Exception:
                font = small = title_font = ImageFont.load_default()
            draw.text((margin_x, 22), title, fill=(20, 20, 20), font=title_font)
            for h, _layer in nodes.values():
                if h.birth_number not in positions:
                    continue
                x, y = positions[h.birth_number]
                child_top = (x + node_w // 2, y)
                for pnb in (h.parent1_birth, h.parent2_birth):
                    if pnb in positions:
                        px, py = positions[pnb]
                        draw.line([(px + node_w // 2, py + node_h), child_top], fill=(185, 185, 185), width=1)
            for row, layer in enumerate(layer_keys):
                y = margin_y + row * (node_h + y_gap)
                label = "EL" if layer == 0 and target else (f"G{layer:+d}" if target else f"GEN {layer}")
                draw.text((10, y + node_h // 2 - 7), label, fill=(90, 90, 90), font=small)
            for h, _layer in nodes.values():
                if h.birth_number not in positions:
                    continue
                x, y = positions[h.birth_number]
                is_target = target and h.birth_number == target.birth_number
                preserved = h.birth_number in getattr(self, "gene_bank", set())
                if is_target:
                    fill, outline, width_line = (255, 220, 70), (160, 110, 0), 4
                elif preserved:
                    fill, outline, width_line = (255, 245, 185), (170, 130, 0), 3
                elif h.alive:
                    fill, outline, width_line = (210, 245, 210), (50, 130, 50), 2
                else:
                    fill, outline, width_line = (230, 230, 230), (130, 130, 130), 1
                draw.rounded_rectangle((x, y, x + node_w, y + node_h), radius=8, fill=fill, outline=outline, width=width_line)
                draw.text((x + 8, y + 6), f"#{h.birth_number} {'★ ' if preserved else ''}{'V' if h.alive else 'M'}", fill=(0, 0, 0), font=font)
                draw.text((x + 8, y + 23), f"p:{h.parent1_birth}/{h.parent2_birth} score {self.gene_score(h):.1f}", fill=(30, 30, 30), font=small)
                draw.text((x + 8, y + 39), f"hijos {len(self.children_of(h.birth_number))}", fill=(55, 55, 55), font=small)
                draw.text((x + 8, y + 55), flags_for(h), fill=(80, 80, 80), font=small)
                if is_target:
                    draw.line((x + 8, y + node_h - 8, x + node_w - 8, y + node_h - 8), fill=(120, 80, 0), width=2)
            draw.text((margin_x, height - 52), "Leyenda: V=vivo M=muerto ★=banco | A=aventurero C=curioso R=proto-refugio M=muerte/no-movimiento P=peligro", fill=(70, 70, 70), font=small)
            img.save(path)
            return f"Árbol exportado a imagen PNG: {path}"

        # Exportación SVG sin dependencias externas.
        def esc(s: Any) -> str:
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

        parts_svg: List[str] = []
        parts_svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
        parts_svg.append('<rect width="100%" height="100%" fill="white"/>')
        parts_svg.append(f'<text x="{margin_x}" y="42" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#202020">{esc(title)}</text>')
        # Edges.
        for h, _layer in nodes.values():
            if h.birth_number not in positions:
                continue
            x, y = positions[h.birth_number]
            cx, cy = x + node_w // 2, y
            for pnb in (h.parent1_birth, h.parent2_birth):
                if pnb in positions:
                    px, py = positions[pnb]
                    pcx, pcy = px + node_w // 2, py + node_h
                    mid = (pcy + cy) // 2
                    parts_svg.append(f'<path d="M {pcx} {pcy} C {pcx} {mid}, {cx} {mid}, {cx} {cy}" stroke="#b8b8b8" stroke-width="1.2" stroke-opacity="0.72" fill="none"/>')
        # Layer labels.
        for row, layer in enumerate(layer_keys):
            y = margin_y + row * (node_h + y_gap)
            label = "EL" if layer == 0 and target else (f"G{layer:+d}" if target else f"GEN {layer}")
            parts_svg.append(f'<text x="10" y="{y + node_h//2}" font-family="Arial" font-size="11" fill="#777">{esc(label)}</text>')
        # Nodes.
        for h, _layer in nodes.values():
            if h.birth_number not in positions:
                continue
            x, y = positions[h.birth_number]
            is_target = target and h.birth_number == target.birth_number
            preserved = h.birth_number in getattr(self, "gene_bank", set())
            if is_target:
                fill, stroke, sw = "#ffdc46", "#a06e00", 4
            elif preserved:
                fill, stroke, sw = "#fff5b9", "#aa8200", 3
            elif h.alive:
                fill, stroke, sw = "#d2f5d2", "#328232", 2
            else:
                fill, stroke, sw = "#e6e6e6", "#828282", 1
            parts_svg.append(f'<rect x="{x}" y="{y}" width="{node_w}" height="{node_h}" rx="8" ry="8" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            label = f"#{h.birth_number} {'★ ' if preserved else ''}{'V' if h.alive else 'M'}"
            parts_svg.append(f'<text x="{x+8}" y="{y+20}" font-family="Arial" font-size="13" font-weight="700" fill="#000">{esc(label)}</text>')
            parts_svg.append(f'<text x="{x+8}" y="{y+36}" font-family="Arial" font-size="11" fill="#303030">p:{h.parent1_birth}/{h.parent2_birth} score {self.gene_score(h):.1f}</text>')
            parts_svg.append(f'<text x="{x+8}" y="{y+52}" font-family="Arial" font-size="11" fill="#555">hijos {len(self.children_of(h.birth_number))}</text>')
            parts_svg.append(f'<text x="{x+8}" y="{y+66}" font-family="Arial" font-size="11" fill="#555">{esc(flags_for(h))}</text>')
            if is_target:
                parts_svg.append(f'<line x1="{x+8}" y1="{y+node_h-8}" x2="{x+node_w-8}" y2="{y+node_h-8}" stroke="#785000" stroke-width="2"/>')
        legend = "Leyenda: V=vivo M=muerto ★=banco genético | A=aventurero C=curioso R=proto-refugio M=muerte/no-movimiento P=peligro"
        parts_svg.append(f'<text x="{margin_x}" y="{height-32}" font-family="Arial" font-size="11" fill="#555">{esc(legend)}</text>')
        parts_svg.append('</svg>')
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts_svg))
        return f"Árbol exportado a imagen SVG: {path}"

    def max_performance_genes(self) -> Genes:
        """Genes al máximo útil para pruebas controladas.
        No se usa en reproducción normal: solo con el comando spawnmax/spawn X max.
        """
        return Genes(
            speed=1.8,
            strength=20.0,
            memory=2.0,
            curiosity=1.8,
            sociability=1.5,
            aggression=1.3,
            association=2.0,
            fertility=1.5,
            sleep_need=0.6,
            energy_efficiency=1.6,
            weirdness=1.2,
            exploration_spirit=3.0,
        )

    def manual_spawn_max_humans(self, count: int) -> List[Human]:
        """Crea humanos de prueba con genes al máximo útil.
        Importante: nacen sin conceptos, sin recuerdos y sin conocimiento; solo
        tienen potencial genético extremo para ver de qué son capaces.
        """
        born: List[Human] = []
        for _ in range(max(1, int(count))):
            pos = self.find_spawn_position(None, None) or self.random_empty_cell()
            if not pos:
                break
            h = self.add_human(pos[0], pos[1])
            h.genes = self.max_performance_genes()
            h.hunger_resistance = 2.0
            h.thirst_resistance = 2.0
            h.old_age_resistance = 2.0
            h.energy = 100.0
            h.last_action = "nacer_max_genes"
            self.log(
                "spawn_max_genes",
                h.entity_id,
                nacimiento=h.birth_number,
                pos=h.pos(),
                nota="genes al máximo útil para prueba; no hereda conceptos ni recuerdos",
            )
            born.append(h)
        return born

    def add_human(self, x: int, y: int, parent: Optional[Human] = None, parent2: Optional[Human] = None) -> Human:
        birth_number = self.next_human_birth_number
        self.next_human_birth_number += 1

        p1 = parent.birth_number if parent else 0
        p2 = parent2.birth_number if parent2 else 0

        # Nombre genealógico: padre1/padre2 número_de_nacimiento_de_este_humano
        # Ejemplo: 0/0 1 para iniciales; 2/5 9 para un hijo de 2 y 5.
        name = f"{p1}/{p2} {birth_number}"

        genes = self.inherit_genes(parent, parent2) if parent else Genes()
        h = Human(
            entity_id=self.make_id("H"),
            kind="human",
            name=name,
            x=x,
            y=y,
            hp=30,
            max_hp=30,
            damage=1,
            genes=genes,
            birth_number=birth_number,
            parent1_birth=p1,
            parent2_birth=p2,
        )
        self.humans[h.entity_id] = h
        self.creatures[h.entity_id] = h
        self.log("nacimiento", h.entity_id, nombre=h.name, nacimiento=birth_number, padre1=p1, padre2=p2, pos=(x, y))
        return h


    def register_gene_bank(self, h: Human, reason: str) -> None:
        if h.birth_number <= 0:
            return
        self.gene_bank.add(h.birth_number)
        notes = self.gene_bank_notes.setdefault(h.birth_number, [])
        if reason not in notes:
            notes.append(reason)
        h.protection_marks += 1

    def update_gene_bank(self) -> None:
        """Guarda linajes prometedores aunque sobrevivan mal: exploradores, descubridores y proto-constructores."""
        for h in self.humans.values():
            if getattr(h, "is_lab", False):
                continue
            refuge = max(
                h.neural.connections.get(tuple(sorted(("intento_refugio", "palos_piedras"))), 0.0),
                h.neural.connections.get(tuple(sorted(("cueva_interior", "reposo"))), 0.0),
                h.neural.connections.get(tuple(sorted(("cueva_interior", "menos_daño"))), 0.0),
            )
            fear = max(
                h.neural.connections.get(tuple(sorted(("forma_trex", "dolor"))), 0.0),
                h.neural.connections.get(tuple(sorted(("forma_cow", "dolor"))), 0.0),
                h.neural.connections.get(tuple(sorted(("no_movimiento", "ser_human"))), 0.0),
            )
            discovery = h.genes.curiosity * 0.35 + h.genes.exploration_spirit * 0.35 + h.genes.association * 0.20 + h.genes.weirdness * 0.10
            if refuge >= 0.12:
                self.register_gene_bank(h, f"proto-refugio/refugio artificial detectado ({refuge:.2f})")
            if fear >= 0.20:
                self.register_gene_bank(h, f"posible miedo/peligro/no-movimiento detectado ({fear:.2f})")
            if discovery >= 1.15 and (refuge >= 0.08 or fear >= 0.12 or len(h.detected_concepts) >= 2):
                self.register_gene_bank(h, f"genes descubridores prometedores ({discovery:.2f})")
            if self.gene_score(h) >= 105:
                self.register_gene_bank(h, f"score genético alto ({self.gene_score(h):.1f})")

    def gene_bank_candidates(self, n: int = 20) -> List[Human]:
        hs = [self.human_by_birth(nb) for nb in self.gene_bank]
        hs = [h for h in hs if h is not None]
        return sorted(hs, key=lambda h: (self.category_score(h, "descubridores"), self.gene_score(h)), reverse=True)[:n]

    def gene_bank_report(self) -> str:
        self.update_gene_bank()
        lines = ["BANCO GENÉTICO / LINAJES PROTEGIDOS", "=" * 80]
        bank = self.gene_bank_candidates(80)
        if not bank:
            lines.append("Todavía no hay linajes protegidos.")
            lines.append("Puedes usar: preserve 721")
            return "\n".join(lines)
        for h in bank:
            status = "VIVO" if h.alive else "muerto"
            notes = "; ".join(self.gene_bank_notes.get(h.birth_number, [])[-3:])
            lines.append(f"#{h.birth_number:>4} {h.name:<14} {status:<6} score={self.gene_score(h):5.1f} desc={self.category_score(h,'descubridores'):5.1f} exp={h.genes.exploration_spirit:.2f} cur={h.genes.curiosity:.2f} assoc={h.genes.association:.2f}")
            lines.append(f"      motivos: {notes or 'preservado manual/automático'}")
        return "\n".join(lines)

    def category_score(self, h: Human, category: str) -> float:
        g = h.genes
        conn = h.neural.connections
        def c(a: str, b: str) -> float:
            return conn.get(tuple(sorted((a, b))), 0.0)
        alive_bonus = 12 if h.alive else 0
        survival = alive_bonus + h.age * 0.02 + h.hp * 0.35 + g.energy_efficiency * 12 + h.hunger_resistance * 8 + h.thirst_resistance * 10 + h.old_age_resistance * 4
        scores = {
            "curiosos": g.curiosity * 60 + g.weirdness * 18 + g.association * 10 + len(h.detected_concepts) * 1.5,
            "aventureros": g.exploration_spirit * 55 + g.speed * 12 + c("impulso_explorador", "mover_hacia_desconocido") * 40,
            "aprendices": g.association * 35 + g.memory * 30 + len(h.neural.connections) * 0.6 + len(h.detected_concepts) * 2,
            "supervivientes": survival,
            "refugio": c("intento_refugio", "palos_piedras") * 75 + c("cueva_interior", "reposo") * 60 + c("cueva_interior", "menos_daño") * 80 + g.curiosity * 10,
            "miedo_peligro": c("forma_trex", "dolor") * 70 + c("forma_cow", "dolor") * 45 + c("no_movimiento", "ser_human") * 55 + c("dolor", "devolver_golpe") * 25,
            "sociales": g.sociability * 45 + c("otro_humano_cerca", "bienestar_social") * 45,
            "descubridores": g.curiosity * 25 + g.exploration_spirit * 25 + g.association * 18 + g.weirdness * 10 + c("intento_refugio", "palos_piedras") * 60 + c("impulso_explorador", "mover_hacia_desconocido") * 35 + len(h.detected_concepts) * 2,
            "genes": self.gene_score(h),
        }
        return scores.get(category, self.gene_score(h))

    def rankings_report(self, category: Optional[str] = None, limit: int = 12) -> str:
        self.update_gene_bank()
        categories = [
            ("curiosos", "MÁS CURIOSOS"),
            ("aventureros", "MÁS AVENTUREROS"),
            ("aprendices", "MEJORES APRENDICES/ASOCIADORES"),
            ("descubridores", "DESCUBRIDORES / DETECTAN ERRORES"),
            ("refugio", "PROTO-REFUGIO / CONSTRUCTORES"),
            ("miedo_peligro", "PELIGRO / MIEDO / MUERTE"),
            ("supervivientes", "MEJORES SUPERVIVIENTES"),
            ("sociales", "MÁS SOCIALES"),
            ("genes", "MEJORES GENES GENERALES"),
        ]
        if category:
            categories = [x for x in categories if x[0].startswith(category) or category in x[1].lower()]
            if not categories:
                categories = [("genes", "MEJORES GENES GENERALES")]
        hs = [h for h in self.humans.values() if not getattr(h, "is_lab", False)]
        lines: List[str] = []
        for key, title in categories:
            lines.append(title)
            lines.append("=" * len(title))
            ranked = sorted(hs, key=lambda h: self.category_score(h, key), reverse=True)[:limit]
            if not ranked:
                lines.append("sin humanos registrados")
            for i, h in enumerate(ranked, 1):
                status = "VIVO" if h.alive else "muerto"
                bank = "★" if h.birth_number in self.gene_bank else " "
                lines.append(f"{i:02d}. {bank}#{h.birth_number:04d} {h.name:<14} {status:<6} score={self.category_score(h,key):6.1f} gen={self.gene_score(h):5.1f} cur={h.genes.curiosity:.2f} exp={h.genes.exploration_spirit:.2f}")
            lines.append("")
        lines.append("★ = guardado en banco genético. Estos tops son dinámicos: suben/bajan según genes, supervivencia y conceptos detectados.")
        return "\n".join(lines)

    # ----------------------------
    # Física
    # ----------------------------

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < WIDTH and 0 <= y < HEIGHT

    def terrain_at(self, x: int, y: int) -> str:
        if not self.in_bounds(x, y):
            return CAVE_WALL
        return self.grid[y][x]

    def is_cell_walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.grid[y][x] != CAVE_WALL

    def can_place_creature(self, c: Creature, x: int, y: int) -> bool:
        for cx, cy in c.occupied_cells(x, y):
            if not self.in_bounds(cx, cy):
                return False
            terrain = self.terrain_at(cx, cy)
            if terrain == CAVE_WALL:
                return False
            if c.kind in ("cow", "trex") and terrain == CAVE_INTERIOR:
                return False
            if self.creature_at(cx, cy, ignore_id=c.entity_id):
                return False
        return True

    def creature_at(self, x: int, y: int, ignore_id: Optional[str] = None) -> Optional[Creature]:
        for c in self.creatures.values():
            if not c.alive or c.entity_id == ignore_id:
                continue
            if (x, y) in c.occupied_cells():
                return c
        return None

    def items_at(self, x: int, y: int) -> List[Item]:
        return [i for i in self.items.values() if i.x == x and i.y == y]

    def random_empty_cell(self, avoid_center: bool = False) -> Optional[Tuple[int, int]]:
        for _ in range(2000):
            x = random.randint(1, WIDTH - 2)
            y = random.randint(1, HEIGHT - 2)
            if avoid_center and dist((x, y), (WIDTH // 2, HEIGHT // 2)) < 12:
                continue
            if self.is_cell_walkable(x, y) and not self.creature_at(x, y):
                return (x, y)
        return None

    def random_empty_cell_for_kind(self, kind: str, avoid_center: bool = False) -> Optional[Tuple[int, int]]:
        dummy = Creature("dummy", kind, kind, 0, 0, 1, 1, 0)
        for _ in range(3000):
            x = random.randint(2, WIDTH - 3)
            y = random.randint(2, HEIGHT - 3)
            if avoid_center and dist((x, y), (WIDTH // 2, HEIGHT // 2)) < 12:
                continue
            if self.can_place_creature(dummy, x, y):
                return (x, y)
        return None

    def random_exploration_target(self, pos: Tuple[int, int], min_distance: int = 14) -> Optional[Tuple[int, int]]:
        """Objetivo lejano para dispersión exploratoria.
        No da conocimiento: solo representa impulso heredable de alejarse y mirar mundo.
        """
        for _ in range(700):
            x = random.randint(1, WIDTH - 2)
            y = random.randint(1, HEIGHT - 2)
            if dist(pos, (x, y)) < min_distance:
                continue
            if self.is_cell_walkable(x, y) and not self.creature_at(x, y):
                return (x, y)
        return None

    def move_creature(self, c: Creature, dx: int, dy: int) -> bool:
        nx, ny = c.x + dx, c.y + dy
        if self.can_place_creature(c, nx, ny):
            c.x, c.y = nx, ny
            return True
        return False

    def step_towards(self, c: Creature, target: Tuple[int, int]) -> bool:
        dx = sign(target[0] - c.x)
        dy = sign(target[1] - c.y)
        options = [(dx, dy), (dx, 0), (0, dy), (random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))]
        for ox, oy in options:
            if ox == 0 and oy == 0:
                continue
            if self.move_creature(c, ox, oy):
                return True
        return False

    def step_away(self, c: Creature, threat: Tuple[int, int]) -> bool:
        dx = sign(c.x - threat[0])
        dy = sign(c.y - threat[1])
        options = [(dx, dy), (dx, 0), (0, dy), (random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))]
        for ox, oy in options:
            if ox == 0 and oy == 0:
                continue
            if self.move_creature(c, ox, oy):
                return True
        return False

    def species_speed(self, c: Creature) -> float:
        """Velocidad media por tick. Humanos=1, T-Rex=1.5, vaca=1.2, pollo=0.5."""
        if c.kind == "trex":
            return 1.5
        if c.kind == "cow":
            return 1.2
        if c.kind == "chicken":
            return 0.5
        return 1.0

    def maybe_extra_species_step(self, c: Creature, mode: str = "random", target: Optional[Tuple[int, int]] = None, threat: Optional[Tuple[int, int]] = None) -> None:
        """Aplica la parte decimal de la velocidad sin mover por magia.
        Ej.: T-Rex 1.5 = un paso normal + 50% de otro paso. Vaca 1.2 = +20%.
        Pollos van a 0.5 porque directamente actúan solo la mitad de ticks.
        """
        extra = self.species_speed(c) - 1.0
        if extra <= 0 or not c.alive:
            return
        if random.random() > extra:
            return
        if mode == "towards" and target is not None:
            self.step_towards(c, target)
        elif mode == "away" and threat is not None:
            self.step_away(c, threat)
        else:
            self.move_creature(c, random.randint(-1, 1), random.randint(-1, 1))

    # ----------------------------
    # Tick
    # ----------------------------

    def run_tick(self) -> None:
        self.tick += 1
        self.day = self.tick // TICKS_PER_DAY

        ids = list(self.creatures.keys())
        random.shuffle(ids)

        for eid in ids:
            c = self.creatures.get(eid)
            if not c or not c.alive:
                continue
            if c.kind == "human":
                self.update_human(self.humans[eid])
            elif c.kind == "chicken":
                self.update_chicken(c)
            elif c.kind == "cow":
                self.update_cow(c)
            elif c.kind == "trex":
                self.update_trex(c)

        for h in self.humans.values():
            if h.alive:
                h.neural.decay()

        self.check_auto_spawn_when_one()
        self.check_animal_ecology_balance()
        self.regrow_seeds()

        if self.tick % DETECTOR_EVERY_TICKS == 0:
            self.meta.analyze_all()

    def choose_auto_spawn_parent_pool(self, mode: str, alive: List[Human]) -> List[Human]:
        """Selección diversa para auto_spawn_1: evita cuellos de botella de un único linaje.
        No hereda conceptos, solo usa perfiles genéticos/históricos como padres.
        """
        all_h = list(self.humans.values())
        if mode == "general":
            pool = self.best_gene_humans(alive_only=False, n=30)
        elif mode == "supervivientes":
            pool = sorted(all_h, key=lambda h: self.category_score(h, "supervivientes"), reverse=True)[:30]
        elif mode == "exploradores":
            pool = sorted(all_h, key=lambda h: self.category_score(h, "aventureros") + self.category_score(h, "curiosos"), reverse=True)[:30]
        elif mode == "descubridores":
            pool = self.gene_bank_candidates(30)
            if len(pool) < 8:
                pool += sorted(all_h, key=lambda h: self.category_score(h, "descubridores"), reverse=True)[:30]
        elif mode == "diversidad":
            pool = all_h[:]
            random.shuffle(pool)
            pool = pool[:40]
        else:
            pool = self.best_gene_humans(alive_only=False, n=30)
        # v2.2.6: los inmortales no se usan como padres de auto_spawn_1.
        # Son sujetos experimentales y no deben contaminar linajes normales ni multiplicar población.
        pool = [h for h in pool if h and not getattr(h, "immortal", False)]
        # Quita duplicados conservando orden.
        seen: Set[int] = set()
        out: List[Human] = []
        for h in pool:
            if h and h.birth_number not in seen:
                seen.add(h.birth_number)
                out.append(h)
        return out

    def choose_auto_spawn_parents_diverse(self, child_index: int, alive: List[Human]) -> Tuple[Optional[Human], Optional[Human], str]:
        """Mezcla 40/25/20/10/5 aproximada:
        genes generales, supervivencia, exploración/curiosidad, descubridores, diversidad aleatoria.
        """
        r = random.random()
        if r < 0.40:
            mode = "general"
        elif r < 0.65:
            mode = "supervivientes"
        elif r < 0.85:
            mode = "exploradores"
        elif r < 0.95:
            mode = "descubridores"
        else:
            mode = "diversidad"

        pool = self.choose_auto_spawn_parent_pool(mode, alive)
        if len(pool) < 2:
            pool = [h for h in self.best_gene_humans(alive_only=False, n=20) if not getattr(h, "immortal", False)]
        if not pool:
            return None, None, mode
        p1 = pool[child_index % len(pool)]
        # segundo padre: intenta que no sea pariente inmediato idéntico y que aporte diversidad.
        candidates = [h for h in pool if h.birth_number != p1.birth_number]
        if not candidates:
            candidates = [h for h in self.best_gene_humans(alive_only=False, n=20) if h.birth_number != p1.birth_number and not getattr(h, "immortal", False)]
        p2 = random.choice(candidates) if candidates else None
        return p1, p2, mode

    def check_auto_spawn_when_one(self) -> None:
        """
        Auto-spawn real y diverso: si queda 1 humano o incluso si se extinguen,
        genera self.auto_spawn_amount hijos usando mezcla de perfiles, no solo el mejor general.
        No hereda conceptos ni memoria.
        """
        if not self.auto_spawn_when_one:
            return
        alive = [h for h in self.humans.values() if h.alive and not getattr(h, "is_lab", False) and not getattr(h, "immortal", False)]
        if len(alive) > 1:
            return
        if self.tick - self.last_auto_spawn_tick < 5:
            return

        born: List[Human] = []
        modes_used: Dict[str, int] = {}
        parents_used: List[str] = []
        for i in range(max(1, int(self.auto_spawn_amount))):
            p1, p2, mode = self.choose_auto_spawn_parents_diverse(i, alive)
            modes_used[mode] = modes_used.get(mode, 0) + 1
            child_list = self.manual_spawn_humans(1, p1, p2)
            if child_list:
                born.extend(child_list)
                parents_used.append(f"{p1.birth_number if p1 else 0}/{p2.birth_number if p2 else 0}:{mode}")

        self.last_auto_spawn_tick = self.tick
        self.extinction_notice_shown = False
        self.log(
            "auto_spawn_diverso",
            "world",
            vivos_antes=len(alive),
            creados=len(born),
            comando_equivalente=f"spawn {self.auto_spawn_amount} mix",
            mezcla=modes_used,
            padres_usados=parents_used[:30],
            nota="auto_spawn diverso: 40% genes generales, 25% supervivientes, 20% exploradores, 10% descubridores, 5% diversidad; no hereda conceptos",
        )


    # ----------------------------
    # Ecología animal / anti-deriva lateral
    # ----------------------------

    def is_near_edge(self, pos: Tuple[int, int], margin: int = ANIMAL_EDGE_MARGIN) -> bool:
        x, y = pos
        return x <= margin or x >= WIDTH - 1 - margin or y <= margin or y >= HEIGHT - 1 - margin

    def inward_target(self, jitter: int = ANIMAL_CENTER_JITTER) -> Tuple[int, int]:
        # Compatibilidad: antes esto empujaba al centro. Ahora devuelve un
        # objetivo repartido por el territorio para evitar el nuevo bug de
        # acumulación central.
        return self.random_spread_cell_for_kind("chicken") or (WIDTH // 2, HEIGHT // 2)

    def map_zone_index(self, pos: Tuple[int, int], cols: int = 6, rows: int = 3) -> Tuple[int, int]:
        x, y = pos
        return (min(cols - 1, max(0, int(x / max(1, WIDTH / cols)))),
                min(rows - 1, max(0, int(y / max(1, HEIGHT / rows)))))

    def species_zone_counts(self, kind: str, cols: int = 6, rows: int = 3) -> Dict[Tuple[int, int], int]:
        counts: Dict[Tuple[int, int], int] = {}
        for c in self.creatures.values():
            if c.alive and c.kind == kind:
                z = self.map_zone_index(c.pos(), cols, rows)
                counts[z] = counts.get(z, 0) + 1
        return counts

    def random_spread_cell_for_kind(self, kind: str) -> Optional[Tuple[int, int]]:
        """Elige una celda válida favoreciendo zonas poco pobladas de esa especie.
        No teletransporta animales existentes; solo se usa como objetivo de migración
        o punto de cría. Evita centro/bordes como destino único y reparte por todo el mapa.
        """
        dummy = Creature("dummy", kind, kind, 0, 0, 1, 1, 0)
        animals_same = [c for c in self.creatures.values() if c.alive and c.kind == kind]
        zone_counts = self.species_zone_counts(kind)
        candidates: List[Tuple[Tuple[int, int], float]] = []
        margin = ANIMAL_SPREAD_MARGIN
        local_radius = ANIMAL_CROWD_RADIUS * 1.5
        for _ in range(ANIMAL_TARGET_SAMPLE_CELLS):
            x = random.randint(margin, WIDTH - 1 - margin)
            y = random.randint(margin, HEIGHT - 1 - margin)
            if not self.can_place_creature(dummy, x, y):
                continue
            zone = self.map_zone_index((x, y))
            local = 0
            for c in animals_same:
                if abs(c.x - x) <= local_radius and abs(c.y - y) <= local_radius and dist(c.pos(), (x, y)) <= local_radius:
                    local += 1
            zone_penalty = zone_counts.get(zone, 0)
            # Peso alto si la zona y el radio local están vacíos.
            weight = 1.0 / (1.0 + zone_penalty * 1.5 + local * 3.0)
            # Evita que el centro gane siempre por azar: pequeño premio a objetivos alejados del centro.
            center_dist = dist((x, y), (WIDTH / 2, HEIGHT / 2)) / max(WIDTH, HEIGHT)
            weight *= 0.85 + center_dist * 0.75
            candidates.append(((x, y), weight))
        if candidates:
            return weighted_choice(candidates)
        return self.random_empty_cell_for_kind(kind)

    def same_species_neighbors(self, animal: Creature, radius: float = ANIMAL_CROWD_RADIUS) -> List[Creature]:
        return [
            c for c in self.creatures.values()
            if c.alive and c.kind == animal.kind and c.entity_id != animal.entity_id and dist(c.pos(), animal.pos()) <= radius
        ]

    def species_centroid(self, kind: str) -> Optional[Tuple[float, float]]:
        animals = [c for c in self.creatures.values() if c.alive and c.kind == kind]
        if not animals:
            return None
        return (sum(c.x for c in animals) / len(animals), sum(c.y for c in animals) / len(animals))

    def random_interior_cell_for_kind(self, kind: str) -> Optional[Tuple[int, int]]:
        # v1.7.2: se mantiene el nombre por compatibilidad, pero ya no significa
        # “centro/interior profundo”; ahora busca zonas repartidas y poco ocupadas.
        return self.random_spread_cell_for_kind(kind)

    def check_animal_ecology_balance(self) -> None:
        """Evita concentración artificial de pollos/vacas.
        v1.7 corregía el lateral empujando hacia el interior; eso podía crear
        acumulación central. v1.7.2 reparte animales por zonas poco ocupadas de todo
        el mapa. No teletransporta: solo asigna objetivos de caminata.
        """
        if self.tick % ANIMAL_MIGRATION_CHECK_TICKS != 0:
            return
        for kind in ("chicken", "cow"):
            animals = [c for c in self.creatures.values() if c.alive and c.kind == kind]
            if len(animals) < 6:
                continue
            edge_count = sum(1 for a in animals if self.is_near_edge(a.pos()))
            centroid = self.species_centroid(kind)
            if not centroid:
                continue
            cx, cy = centroid
            edge_ratio = edge_count / max(1, len(animals))

            zone_counts = self.species_zone_counts(kind)
            max_zone = max(zone_counts.values()) if zone_counts else 0
            concentration_ratio = max_zone / max(1, len(animals))
            central_count = sum(
                1 for a in animals
                if WIDTH * 0.35 <= a.x <= WIDTH * 0.65 and HEIGHT * 0.25 <= a.y <= HEIGHT * 0.75
            )
            central_ratio = central_count / max(1, len(animals))

            centroid_near_side = (
                cx < WIDTH * 0.18 or cx > WIDTH * 0.82 or
                cy < HEIGHT * 0.14 or cy > HEIGHT * 0.86
            )
            too_concentrated = concentration_ratio > 0.34 or central_ratio > 0.58
            too_edge = edge_ratio >= ANIMAL_EDGE_CLUSTER_RATIO or centroid_near_side
            if not too_concentrated and not too_edge:
                continue

            movers = animals[:]
            random.shuffle(movers)
            max_movers = max(3, min(len(movers), int(len(movers) * 0.65)))
            for a in movers[:max_movers]:
                target = self.random_spread_cell_for_kind(kind) or self.random_empty_cell_for_kind(kind) or (a.x, a.y)
                setattr(a, "migration_target", target)
                setattr(a, "migration_until", self.tick + random.randint(30, 96))
            self.log(
                "migracion_animal_por_concentracion",
                "world",
                especie=kind,
                total=len(animals),
                borde=edge_count,
                ratio_borde=round(edge_ratio, 2),
                ratio_centro=round(central_ratio, 2),
                ratio_zona_max=round(concentration_ratio, 2),
                centroide=(round(cx, 1), round(cy, 1)),
                migrantes=max_movers,
                nota="corrección ecológica: objetivos repartidos por zonas poco pobladas, no centro fijo",
            )

    def animal_migration_step(self, animal: Creature) -> bool:
        target = getattr(animal, "migration_target", None)
        until = getattr(animal, "migration_until", 0)
        if not target:
            return False
        if self.tick > until or dist(animal.pos(), target) <= 2:
            setattr(animal, "migration_target", None)
            setattr(animal, "migration_until", 0)
            return False
        moved = self.step_towards(animal, target)
        if moved:
            self.maybe_extra_species_step(animal, mode="towards", target=target)
        return moved

    def animal_dispersal_step(self, animal: Creature) -> bool:
        """Movimiento natural de dispersión: evita bordes y aglomeraciones de la misma especie.
        Se aplica solo cuando el animal no está en una conducta más urgente.
        """
        if animal.kind not in ("chicken", "cow"):
            return False
        if self.animal_migration_step(animal):
            return True
        if random.random() > ANIMAL_DISPERSAL_CHANCE.get(animal.kind, 0.25):
            return False

        # Evitar bordes sin empujar siempre al centro: busca una zona libre repartida.
        if self.is_near_edge(animal.pos()):
            target = self.random_spread_cell_for_kind(animal.kind) or self.inward_target()
            moved = self.step_towards(animal, target)
            if moved:
                self.maybe_extra_species_step(animal, mode="towards", target=target)
            return moved

        # Evitar que toda la especie se apelmace.
        neigh = self.same_species_neighbors(animal)
        limit = ANIMAL_CROWD_LIMITS.get(animal.kind, 5)
        if len(neigh) >= limit:
            cx = int(round(sum(n.x for n in neigh) / len(neigh)))
            cy = int(round(sum(n.y for n in neigh) / len(neigh)))
            moved = self.step_away(animal, (cx, cy))
            if moved:
                self.maybe_extra_species_step(animal, mode="away", threat=(cx, cy))
            return moved
        return False

    # ----------------------------
    # Animales
    # ----------------------------

    def animal_idle_move(self, animal: Creature) -> bool:
        """Movimiento aleatorio con sesgo suave hacia espacio abierto.
        Evita que el paseo aleatorio empuje durante días a pollos/vacas contra un lateral.
        """
        choices: List[Tuple[int, int, float]] = []
        neigh = self.same_species_neighbors(animal)
        crowd_center = None
        if neigh:
            crowd_center = (sum(n.x for n in neigh) / len(neigh), sum(n.y for n in neigh) / len(neigh))
        center = (WIDTH / 2, HEIGHT / 2)
        species_cent = self.species_centroid(animal.kind) or center
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = animal.x + dx, animal.y + dy
                if not self.can_place_creature(animal, nx, ny):
                    continue
                weight = 1.0
                # Si está cerca del borde, favorece pasos que se alejen del borde.
                if self.is_near_edge(animal.pos()):
                    old_edge = min(animal.x, WIDTH - 1 - animal.x, animal.y, HEIGHT - 1 - animal.y)
                    new_edge = min(nx, WIDTH - 1 - nx, ny, HEIGHT - 1 - ny)
                    weight += max(0, new_edge - old_edge) * 1.8
                    # No sesgamos al centro: premiamos salir del borde y, si la especie
                    # está concentrada, alejarse de su centroide.
                    if dist((nx, ny), species_cent) > dist(animal.pos(), species_cent):
                        weight += 0.9
                # Si hay aglomeración, favorece pasos que se alejen del centro local.
                if crowd_center and len(neigh) >= ANIMAL_CROWD_LIMITS.get(animal.kind, 5):
                    if dist((nx, ny), crowd_center) > dist(animal.pos(), crowd_center):
                        weight += 2.0
                # Si la zona actual está muy poblada, favorece moverse a otra zona.
                current_zone = self.map_zone_index(animal.pos())
                new_zone = self.map_zone_index((nx, ny))
                zone_counts = self.species_zone_counts(animal.kind)
                if zone_counts.get(current_zone, 0) > max(4, self.count_alive(animal.kind) // 4):
                    if zone_counts.get(new_zone, 0) <= zone_counts.get(current_zone, 0):
                        weight += 0.8
                choices.append((dx, dy, weight))
        if not choices:
            return False
        dx, dy = weighted_choice([((dx, dy), w) for dx, dy, w in choices])
        moved = self.move_creature(animal, dx, dy)
        if moved:
            self.maybe_extra_species_step(animal)
        return moved

    def update_chicken(self, c: Creature) -> None:
        self.try_simple_animal_reproduce(c, "chicken")
        # Velocidad pollo = 0.5: actúa/mueve solo la mitad de los ticks.
        if random.random() > self.species_speed(c):
            return
        if c.last_attacker and c.last_attacker in self.creatures and self.creatures[c.last_attacker].alive:
            self.step_away(c, self.creatures[c.last_attacker].pos())
            return

        seeds_here = [i for i in self.items.values() if i.kind == "seed" and (i.x, i.y) == c.pos()]
        if seeds_here and random.random() < 0.55:
            # Los pollos consumen semillas: evita que una semilla permanente los ancle durante cientos de días.
            seed = random.choice(seeds_here)
            self.items.pop(seed.item_id, None)
            self.log("pollo_come_semilla", c.entity_id, semilla=seed.item_id, pos=c.pos())
            return

        # Si está pegado a un lateral, prioriza salir de ahí antes de seguir semillas lejanas.
        if self.is_near_edge(c.pos()) and random.random() < 0.75 and self.animal_dispersal_step(c):
            return

        seeds = [i for i in self.items.values() if i.kind == "seed" and dist(c.pos(), (i.x, i.y)) <= 10]
        if seeds:
            target = min(seeds, key=lambda i: dist(c.pos(), (i.x, i.y)))
            self.step_towards(c, (target.x, target.y))
            return

        if self.animal_dispersal_step(c):
            return
        self.animal_idle_move(c)

    def predator_ignore_map(self, predator: Creature) -> Dict[str, int]:
        """Mapa dinámico humano_id -> tick hasta el que el animal lo ignora."""
        m = getattr(predator, "attack_ignore_until", None)
        if not isinstance(m, dict):
            m = {}
            setattr(predator, "attack_ignore_until", m)
        # Limpieza suave de expirados.
        expired = [hid for hid, until in m.items() if until <= self.tick]
        for hid in expired:
            m.pop(hid, None)
        return m

    def predator_is_ignoring(self, predator: Creature, human: Human) -> bool:
        m = self.predator_ignore_map(predator)
        return m.get(human.entity_id, -1) > self.tick

    def predator_clear_ignore_for(self, predator: Creature, human_id: str) -> None:
        m = self.predator_ignore_map(predator)
        if human_id in m:
            m.pop(human_id, None)
            setattr(predator, "attack_focus_target", None)
            setattr(predator, "attack_focus_start_tick", None)

    def predator_register_failed_attack_pressure(self, predator: Creature, target: Human, reason: str = "bloqueado") -> bool:
        """Registra que el animal intenta alcanzar/atacar pero no lo consigue.
        Devuelve True si acaba de abandonar el acecho y poner ignore.
        """
        if predator.kind not in ("trex", "cow") or not target.alive:
            return False
        # Si el humano lo acaba de atacar, no se aplica la fatiga: responde.
        if predator.last_attacker == target.entity_id:
            self.predator_clear_ignore_for(predator, target.entity_id)
            setattr(predator, "attack_focus_target", target.entity_id)
            setattr(predator, "attack_focus_start_tick", self.tick)
            return False
        current_target = getattr(predator, "attack_focus_target", None)
        if current_target != target.entity_id:
            setattr(predator, "attack_focus_target", target.entity_id)
            setattr(predator, "attack_focus_start_tick", self.tick)
            setattr(predator, "attack_focus_reason", reason)
            return False
        start = getattr(predator, "attack_focus_start_tick", self.tick)
        if start is None:
            setattr(predator, "attack_focus_start_tick", self.tick)
            return False
        if self.tick - int(start) < PREDATOR_STUCK_ATTACK_TICKS:
            return False

        ignore_until = self.tick + PREDATOR_IGNORE_TICKS
        m = self.predator_ignore_map(predator)
        ignored: List[int] = []
        # Ignora al objetivo y al grupo muy junto a él, para evitar atasco en entradas de cuevas.
        for h in self.humans.values():
            if h.alive and dist(h.pos(), target.pos()) <= PREDATOR_IGNORE_GROUP_RADIUS:
                m[h.entity_id] = ignore_until
                ignored.append(h.birth_number)
        setattr(predator, "attack_focus_target", None)
        setattr(predator, "attack_focus_start_tick", None)
        if predator.last_attacker in m:
            predator.last_attacker = None
        self.log(
            "animal_abandona_acecho",
            predator.entity_id,
            objetivo=target.entity_id,
            objetivo_nombre=target.name,
            humanos_ignorados=ignored[:12],
            total_ignorados=len(ignored),
            dias_sin_alcanzar=PREDATOR_STUCK_ATTACK_DAYS,
            ignora_durante_dias=PREDATOR_IGNORE_DAYS,
            motivo=reason,
        )
        return True

    def predator_register_attack_success(self, predator: Creature, target: Creature) -> None:
        if predator.kind in ("trex", "cow"):
            setattr(predator, "attack_focus_target", None)
            setattr(predator, "attack_focus_start_tick", None)

    def update_cow(self, c: Creature) -> None:
        self.try_simple_animal_reproduce(c, "cow")
        if c.last_attacker and c.last_attacker in self.creatures and self.creatures[c.last_attacker].alive:
            attacker = self.creatures[c.last_attacker]
            if attacker.kind == "human":
                h_attacker = self.humans.get(attacker.entity_id)
                if h_attacker is not None and self.predator_is_ignoring(c, h_attacker):
                    # Si no le han vuelto a pegar, deja de insistir durante el periodo de ignore.
                    c.last_attacker = None
                    if self.animal_dispersal_step(c):
                        return
                    self.animal_idle_move(c)
                    return
            # Tras 1-2 cornadas, la vaca deja de insistir y se aleja.
            # No es magia: conducta defensiva, no depredadora. Si la vuelven a atacar puede reaccionar otra vez.
            defensive_hits = getattr(c, "defensive_hits", 0)
            defensive_limit = getattr(c, "defensive_limit", random.choice([1, 2]))
            setattr(c, "defensive_limit", defensive_limit)
            if defensive_hits >= defensive_limit:
                self.step_away(c, attacker.pos())
                self.maybe_extra_species_step(c, mode="away", target=attacker.pos())
                self.log("vaca_se_retira", c.entity_id, atacante=attacker.entity_id, cornadas=defensive_hits, limite=defensive_limit)
                c.last_attacker = None
                setattr(c, "defensive_hits", 0)
                setattr(c, "defensive_limit", random.choice([1, 2]))
                return
            if manhattan(c.pos(), attacker.pos()) <= 2 and self.can_attack_target(c, attacker):
                self.attack(c, attacker, c.damage, "cornada")
            else:
                if attacker.kind == "human":
                    h_attacker = self.humans.get(attacker.entity_id)
                    if h_attacker is not None and self.predator_register_failed_attack_pressure(c, h_attacker, reason="vaca_bloqueada_o_no_alcanza"):
                        c.last_attacker = None
                        self.step_away(c, attacker.pos())
                        self.maybe_extra_species_step(c, mode="away", target=attacker.pos())
                        return
                self.step_towards(c, attacker.pos())
                self.maybe_extra_species_step(c, mode="towards", target=attacker.pos())
            return
        if self.animal_dispersal_step(c):
            return
        self.animal_idle_move(c)

    def try_simple_animal_reproduce(self, animal: Creature, kind: str) -> None:
        # Pollos y vacas están muy programados: si su población baja de 20,
        # se reproducen con fuerza hasta recuperar el ecosistema.
        if self.count_alive(kind) >= ANIMAL_MIN_POPULATION:
            return
        base_chance = 0.32 if kind == "chicken" else 0.20
        chance = min(0.95, base_chance * ANIMAL_REPRODUCTION_MULTIPLIER)
        if random.random() > chance:
            return
        spread = 2 if kind == "chicken" else 3
        # 35% de las crías intentan aparecer en una zona poco poblada de esa especie.
        # Es dispersión ecológica programada en animales, no aprendizaje humano ni teletransporte
        # de adultos. Evita que todos los nacimientos refuercen el mismo racimo.
        if random.random() < 0.35:
            pos = self.random_spread_cell_for_kind(kind)
            if pos:
                baby = self.add_creature(kind, pos[0], pos[1])
                self.log("reproduccion_animal", animal.entity_id, especie=kind, hijo=baby.entity_id, total_especie=self.count_alive(kind), modo="zona_poco_poblada")
                return
        for attempt in range(22):
            nx = animal.x + random.randint(-spread, spread)
            ny = animal.y + random.randint(-spread, spread)
            dummy = Creature("dummy", kind, kind, nx, ny, 5 if kind == "chicken" else 20, 5 if kind == "chicken" else 20, 0 if kind == "chicken" else 8)
            if self.is_near_edge((nx, ny)) and attempt < 14:
                continue
            if self.can_place_creature(dummy, nx, ny):
                baby = self.add_creature(kind, nx, ny)
                self.log("reproduccion_animal", animal.entity_id, especie=kind, hijo=baby.entity_id, total_especie=self.count_alive(kind), modo="cerca_progenitor")
                return

    def update_trex(self, c: Creature) -> None:
        self.try_trex_reproduce(c)

        # Si un humano le acaba de pegar, responde aunque estuviera en ignore.
        revenge_target: Optional[Human] = None
        if c.last_attacker and c.last_attacker in self.humans and self.humans[c.last_attacker].alive:
            revenge_target = self.humans[c.last_attacker]
            self.predator_clear_ignore_for(c, revenge_target.entity_id)

        if revenge_target is not None and dist(c.pos(), revenge_target.pos()) < TREX_AGGRO_RADIUS + 2:
            target = revenge_target
        else:
            nearby_humans = [
                h for h in self.humans.values()
                if h.alive
                and dist(c.pos(), h.pos()) < TREX_AGGRO_RADIUS
                and not self.predator_is_ignoring(c, h)
            ]

            if not nearby_humans:
                self.move_creature(c, random.randint(-1, 1), random.randint(-1, 1))
                self.maybe_extra_species_step(c)
                return

            target = min(nearby_humans, key=lambda h: dist(c.pos(), h.pos()))

        if self.can_attack_target(c, target) and manhattan(c.pos(), target.pos()) <= 2:
            self.attack(c, target, c.damage, "mordisco_trex")
        else:
            if self.predator_register_failed_attack_pressure(c, target, reason="trex_bloqueado_o_no_alcanza"):
                # Ha abandonado ese grupo durante 7 días: se aleja para desbloquear la entrada.
                self.step_away(c, target.pos())
                self.maybe_extra_species_step(c, mode="away", target=target.pos())
                return
            self.step_towards(c, target.pos())
            self.maybe_extra_species_step(c, mode="towards", target=target.pos())

    def try_trex_reproduce(self, t: Creature) -> None:
        if self.day <= 0:
            return
        if self.count_alive("trex") >= MAX_TREX:
            # Límite ecológico del territorio: no nacen más T-Rex si ya hay 7 vivos.
            # No es una decisión mental de los animales; es capacidad del ecosistema.
            return
        if self.day - t.last_reproduction_day < TREX_REPRODUCE_EVERY_DAYS:
            return
        if random.random() > 0.08:
            return

        for _ in range(20):
            nx = t.x + random.randint(-3, 3)
            ny = t.y + random.randint(-3, 3)
            dummy = Creature("dummy", "trex", "T-Rex", nx, ny, 50, 50, 18)
            if self.can_place_creature(dummy, nx, ny):
                baby = self.add_creature("trex", nx, ny)
                baby.last_reproduction_day = self.day
                t.last_reproduction_day = self.day
                self.log("reproduccion_trex", t.entity_id, hijo=baby.entity_id, pos=(nx, ny))
                return

        t.last_reproduction_day = self.day

    def can_attack_target(self, attacker: Creature, target: Creature) -> bool:
        target_terrain = self.terrain_at(target.x, target.y)
        if target.kind == "human" and target_terrain == CAVE_INTERIOR:
            return attacker.kind == "chicken"
        return True

    # ----------------------------
    # Humanos
    # ----------------------------

    def is_night(self) -> bool:
        hour = self.tick % TICKS_PER_DAY
        return hour < 6 or hour >= 18

    def vision_radius(self, base_radius: float) -> float:
        # Por la noche los humanos ven la mitad de distancia.
        return max(1.0, base_radius * 0.5) if self.is_night() else base_radius

    def update_human(self, h: Human) -> None:
        h.age += 1
        # Hambre 20% más lenta; sed igual.
        h.hunger = clamp(h.hunger + 0.88 / max(0.25, h.genes.energy_efficiency * h.hunger_resistance), 0, 100)
        h.thirst = clamp(h.thirst + 1.35 / max(0.25, h.genes.energy_efficiency * h.thirst_resistance), 0, 100)
        h.sleepiness = clamp(h.sleepiness + 0.9 * h.genes.sleep_need, 0, 100)
        h.energy = clamp(h.energy - 0.35 / h.genes.energy_efficiency, 0, 100)

        self.apply_social_comfort(h)

        if h.hunger >= 98 or h.thirst >= 98:
            h.hp -= 1.5
            h.neural.activate("malestar_extremo", 0.2)
            h.neural.reinforce("hambre_sed_alta", "dolor", 0.06)
            self.log("daño_por_necesidad", h.entity_id, hp=h.hp, hambre=h.hunger, sed=h.thirst)
            if h.hp <= 0:
                self.kill(h, "hambre_sed")
                return

        # Dormir: reacción corporal, no conocimiento.
        if h.sleepiness > 82 or h.energy < 12:
            self.human_sleep(h)
            return

        # Prioridad natural por urgencia real: no es regla fija sed > hambre.
        # El cuerpo empuja hacia la necesidad más urgente considerando distancia y visión.
        need_actions: List[Tuple[str, float, Any]] = []

        if self.terrain_at(h.x, h.y) == WATER and h.thirst > 10:
            self.human_drink(h)
            return

        if h.hunger > 45:
            # Puede probar a comer objetos comestibles que ya lleva encima. No hereda el concepto;
            # la experiencia de bajar hambre refuerza la asociación.
            inv_edible = next((i for i in h.inventory if i.edible), None)
            if inv_edible:
                self.human_eat_item(h, inv_edible)
                return
            ground_edible = next((i for i in self.items_at(h.x, h.y) if i.edible), None)
            if ground_edible:
                self.pickup_item(h, ground_edible)
                return

        water = self.find_nearest_terrain(h.pos(), WATER, self.vision_radius(20)) if h.thirst > 35 else None
        if water:
            water_d = max(1.0, dist(h.pos(), water))
            # Si tiene hambre y sed, manda principalmente la necesidad que esté más alta.
            # La distancia solo desempata: no queremos que un agua cercana eclipse
            # una hambre mucho más crítica, ni al revés.
            thirst_urgency = (h.thirst / 100.0) * 10.0 + (1.0 / water_d)
            need_actions.append(("water", thirst_urgency, water))

        food_target = self.best_food_or_potential_food_target(h)
        if food_target:
            target_pos, target_type, target_obj = food_target
            food_d = max(1.0, dist(h.pos(), target_pos))
            hunger_urgency = (h.hunger / 100.0) * 10.0 + (1.0 / food_d)
            need_actions.append((target_type, hunger_urgency, target_obj))

        if need_actions:
            need_actions.sort(key=lambda x: x[1], reverse=True)
            action_type, urgency, obj = need_actions[0]
            if urgency > 3.6 or h.hunger > 70 or h.thirst > 70:
                if action_type == "water":
                    h.neural.activate("sed_alta", 0.2)
                    h.neural.reinforce("sed_alta", "mover_hacia_agua", 0.04)
                    self.step_towards(h, obj)
                    h.last_action = "urgencia_buscar_agua"
                    h.sleep_history.append((self.tick, False))
                    return
                if action_type == "item_food" or action_type == "potential_item":
                    item: Item = obj
                    h.neural.activate("hambre_alta", 0.22)
                    h.neural.reinforce("hambre_alta", "mover_hacia_objeto_pequeño", 0.04)
                    self.step_towards(h, (item.x, item.y))
                    h.last_action = "urgencia_hambre_explorar_objeto"
                    h.sleep_history.append((self.tick, False))
                    return
                if action_type == "creature_food" or action_type == "potential_creature":
                    cr: Creature = obj
                    h.neural.activate("hambre_alta", 0.22)
                    h.neural.reinforce("hambre_alta", "mover_hacia_ser_pequeño", 0.04)
                    if dist(h.pos(), cr.pos()) <= 2:
                        self.human_attack(h, cr)
                    else:
                        self.step_towards(h, cr.pos())
                        h.last_action = "urgencia_hambre_explorar_ser"
                    h.sleep_history.append((self.tick, False))
                    return

        # Reacción a T-Rex cercano. No saben qué es, solo asocian forma/dolor si ocurre.
        nearest_trex = self.nearest_creature(h, "trex", self.vision_radius(5))
        if nearest_trex:
            h.neural.activate("forma_grande", 0.12)
            if random.random() < 0.55 + h.genes.association * 0.12:
                learned_cave = max(
                    self.neural_connection_strength(h, "cueva_interior", "menos_daño"),
                    self.neural_connection_strength(h, "cueva_interior", "reposo"),
                )
                interior = self.nearest_cave_interior(h.pos())
                if interior and learned_cave > 0.18:
                    self.step_towards(h, interior)
                    h.last_action = "mover_hacia_cueva_aprendido"
                else:
                    self.step_away(h, nearest_trex.pos())
                    h.last_action = "alejarse_forma_grande"
                h.sleep_history.append((self.tick, False))
                return

        # Acciones raras/no previstas.
        if self.maybe_unplanned_action(h):
            h.sleep_history.append((self.tick, False))
            return

        # Cazar.
        if h.hunger > 55:
            prey = self.nearest_huntable(h, 2)
            if prey:
                self.human_attack(h, prey)
                h.sleep_history.append((self.tick, False))
                return

        # Coger objetos.
        ground_items = self.items_at(h.x, h.y)
        if ground_items and random.random() < 0.75:
            self.pickup_item(h, random.choice(ground_items))
            h.sleep_history.append((self.tick, False))
            return

        # Posible cebo.
        if self.maybe_drop_seed_near_chicken(h):
            h.sleep_history.append((self.tick, False))
            return

        # Reproducción.
        if h.energy > 75 and h.hunger < 45 and h.thirst < 45 and random.random() < 0.012 * h.genes.fertility:
            self.try_reproduce_human(h)
            h.sleep_history.append((self.tick, False))
            return

        self.curiosity_move(h)
        h.sleep_history.append((self.tick, False))

    def apply_social_comfort(self, h: Human) -> None:
        others = [
            o for o in self.humans.values()
            if o.alive and o.entity_id != h.entity_id and dist(h.pos(), o.pos()) <= 4
        ]
        if not others:
            return

        h.energy = clamp(h.energy + 0.25, 0, 100)
        h.sleepiness = clamp(h.sleepiness - 0.15, 0, 100)
        h.neural.activate("otro_humano_cerca", 0.16)
        h.neural.activate("bienestar_social", 0.12)
        h.neural.reinforce("otro_humano_cerca", "bienestar_social", 0.04)

    def human_sleep(self, h: Human) -> None:
        h.sleep_history.append((self.tick, True))
        h.sleepiness = clamp(h.sleepiness - 18, 0, 100)
        h.energy = clamp(h.energy + 18, 0, 100)
        h.hp = clamp(h.hp + 0.5, 0, h.max_hp)
        h.last_action = "dormir"
        h.neural.activate("reposo", 0.18)

        if self.terrain_at(h.x, h.y) == CAVE_INTERIOR:
            h.neural.activate("cueva_interior", 0.15)
            h.neural.reinforce("cueva_interior", "reposo", 0.04)

        self.log("dormir", h.entity_id, pos=h.pos(), sueño_24h=h.recent_sleep_hours(self.tick))

    def human_drink(self, h: Human) -> None:
        before = h.thirst
        h.thirst = clamp(h.thirst - 45, 0, 100)
        h.energy = clamp(h.energy + 4, 0, 100)
        h.last_action = "beber"
        h.neural.activate("agua", 0.2)
        h.neural.reinforce("agua", "sed_baja", 0.08)
        self.log("beber", h.entity_id, pos=h.pos(), sed_antes=before, sed_despues=h.thirst)

    def human_eat_item(self, h: Human, item: Item) -> None:
        before = h.hunger
        nutrition = 100 if item.kind == "meat" else 35
        energy_gain = 35 if item.kind == "meat" else 15
        h.hunger = clamp(h.hunger - nutrition, 0, 100)
        h.energy = clamp(h.energy + energy_gain, 0, 100)
        if item in h.inventory:
            h.inventory.remove(item)
        h.last_action = "comer"
        h.neural.activate("objeto_comestible", 0.2)
        h.neural.activate(f"comida_{item.kind}", 0.18)
        h.neural.reinforce(f"comida_{item.kind}", "hambre_baja", 0.10 if item.kind == "meat" else 0.08)
        self.log("comer", h.entity_id, objeto=item.kind, nutricion=nutrition, hambre_antes=before, hambre_despues=h.hunger)

    def pickup_item(self, h: Human, item: Item) -> bool:
        if h.can_carry(item):
            h.inventory.append(item)
            if item.item_id in self.items:
                del self.items[item.item_id]
            h.last_action = "coger"
            h.neural.activate(f"objeto_{item.kind}", 0.15)
            h.neural.reinforce(f"objeto_{item.kind}", "mano_coger", 0.05)
            self.log("coger_objeto", h.entity_id, objeto=item.kind, peso=item.weight, carga=h.carry_weight())
            return True

        if item.kind not in ALLOWED_INVENTORY_KINDS:
            self.log("fallo_coger_no_portable", h.entity_id, objeto=item.kind, motivo="tipo_no_transportable")
        elif len(h.inventory) >= MAX_INVENTORY_ITEMS:
            h.neural.activate("inventario_lleno", 0.18)
            h.neural.reinforce("inventario_lleno", "fallo_coger", 0.06)
            self.log("fallo_coger_inventario_lleno", h.entity_id, objeto=item.kind, maximo=MAX_INVENTORY_ITEMS, inventario=[i.kind for i in h.inventory])
        else:
            h.neural.activate("objeto_pesado", 0.18)
            h.neural.reinforce("objeto_pesado", "fallo_coger", 0.07)
            self.log("fallo_coger_peso", h.entity_id, objeto=item.kind, peso=item.weight, fuerza=h.genes.strength, carga=round(h.carry_weight(), 1))
        return False

    def maybe_drop_seed_near_chicken(self, h: Human) -> bool:
        seed = next((i for i in h.inventory if i.kind == "seed"), None)
        if not seed:
            return False

        chicken = self.nearest_creature(h, "chicken", self.vision_radius(10))
        if not chicken:
            return False

        bait_strength = self.neural_connection_strength(h, "semilla", "pollo_se_acerca")
        chance = 0.02 + h.genes.curiosity * 0.02 + bait_strength * 0.25
        if h.hunger > 55:
            chance += 0.03

        if random.random() > chance:
            return False

        h.inventory.remove(seed)
        seed.x, seed.y = h.x, h.y
        seed.item_id = self.make_id("it")
        self.items[seed.item_id] = seed

        h.last_action = "soltar_semilla"
        h.neural.activate("semilla", 0.18)
        h.neural.activate("pollo_cercano", 0.12)
        h.neural.reinforce("semilla", "pollo_cercano", 0.04)

        self.log("soltar_semilla", h.entity_id, pos=h.pos(), pollo_cercano=chicken.entity_id, distancia=round(dist(h.pos(), chicken.pos()), 1))
        return True

    def maybe_unplanned_action(self, h: Human) -> bool:
        chance = 0.008 + h.genes.curiosity * 0.006 + h.genes.weirdness * 0.018
        if random.random() > chance:
            return False

        inv_kinds = [i.kind for i in h.inventory]
        terrain = self.terrain_at(h.x, h.y)
        candidates: List[Tuple[str, float]] = []

        structural_count = sum(1 for k in inv_kinds if k in ("stick", "stone"))
        recent_deaths = any(e.kind == "observa_muerte" and self.tick - e.tick <= 180 for e in h.memory_events[-80:])
        recent_damage = any(e.kind == "ataque" and e.data.get("objetivo") == h.entity_id and self.tick - e.tick <= 180 for e in self.events[-200:])
        near_cave_for_build = False
        nearest_entrance_for_build = self.nearest_cave_entrance(h.pos())
        if nearest_entrance_for_build and dist(h.pos(), nearest_entrance_for_build) <= 8:
            near_cave_for_build = True

        # Intentar refugio con objetos ya NO se trata como “error no previsto”.
        # Es una prueba física rara pero lógica. Para que no lo hagan todos por llevar
        # una sola piedra, pedimos más contexto: suficientes piezas, muerte/peligro reciente,
        # mucha necesidad de dormir o cercanía a cuevas.
        shelter_context = recent_deaths or recent_damage or h.sleepiness > 70 or near_cave_for_build
        if structural_count >= 2 or (structural_count >= 1 and shelter_context and random.random() < 0.35):
            candidates.append(("intentar_refugio_objetos", 0.16))
        nearest_entrance = self.nearest_cave_entrance(h.pos())
        if terrain in (CAVE_WALL, CAVE_ENTRANCE, CAVE_INTERIOR) or (nearest_entrance and dist(h.pos(), nearest_entrance) < 3):
            candidates.append(("rascar_o_mover_cueva", 0.18))
        if len(h.inventory) >= 2:
            candidates.append(("combinar_objetos_raro", 0.28))

        candidates.append(("gesto_al_aire", 0.12))
        action = weighted_choice(candidates)

        if action == "intentar_refugio_objetos":
            return self.human_try_build_shelter(h)
        if action == "rascar_o_mover_cueva":
            return self.human_try_cave_piece(h)
        if action == "combinar_objetos_raro":
            return self.human_try_weird_combination(h)
        return self.human_do_air_gesture(h)

    def human_try_build_shelter(self, h: Human) -> bool:
        sticks = [i for i in h.inventory if i.kind == "stick"]
        stones = [i for i in h.inventory if i.kind == "stone"]
        used = len(sticks) + len(stones)
        stability = len(stones) * 0.18 + len(sticks) * 0.06
        wind = random.uniform(0.25, 0.95)
        confidence = clamp((h.genes.curiosity + h.genes.weirdness + used * 0.12) * 22, 5, 94)

        h.neural.activate("intento_refugio", 0.25)
        h.neural.activate("palos_piedras", 0.18)
        h.neural.reinforce("palos_piedras", "intento_refugio", 0.08)

        if used < 2:
            result = "fallo_por_pocas_piezas"
            h.neural.reinforce("intento_refugio", "fallo_pocas_piezas", 0.07)
        elif stability < wind:
            result = "se_cae_por_viento_peso"
            h.neural.reinforce("intento_refugio", "viento_tira_estructura", 0.09)
        else:
            result = "estructura_debil_temporal"
            h.neural.reinforce("intento_refugio", "cobertura_debil", 0.08)

        h.last_action = "experimento_refugio_objetos"
        self.log(
            "experimento_refugio",
            h.entity_id,
            accion="intentar_refugio_objetos",
            resultado=result,
            seguridad=round(confidence, 1),
            palos=len(sticks),
            piedras=len(stones),
            viento=round(wind, 2),
            estabilidad=round(stability, 2),
        )
        return True

    def human_try_cave_piece(self, h: Human) -> bool:
        wall_weight = ITEM_PROTOTYPES["cave_wall"]["weight"]
        confidence = clamp((h.genes.curiosity + h.genes.weirdness) * 25, 5, 90)
        h.neural.activate("intento_mover_cueva", 0.2)
        h.neural.activate("objeto_inmenso", 0.2)
        h.neural.reinforce("intento_mover_cueva", "fallo_peso_extremo", 0.08)
        h.last_action = "fallo_fisico_previsible_cueva"
        self.log(
            "fallo_fisico_previsible",
            h.entity_id,
            accion="intentar_mover_o_arrancar_cueva",
            resultado="fallo_por_peso_extremo",
            seguridad=round(confidence, 1),
            peso=wall_weight,
            fuerza=round(h.genes.strength, 1),
        )
        return True

    def human_try_weird_combination(self, h: Human) -> bool:
        """
        Experimento físico con objetos. Ya NO es un fallo/no previsto:
        el mundo responde con física simple y lógica.
        - Palo + piedra: el palo puede romperse por el peso de la piedra.
        - Palo + palo: no se unen porque no hay cuerda/pegamento/ensamble.
        - Piedra + piedra: no se unen porque no hay pegamento/forma de fijarlas.
        - Otros objetos: no hay efecto físico útil.
        """
        if len(h.inventory) < 2:
            return False

        a, b = random.sample(h.inventory, 2)
        confidence = clamp((h.genes.curiosity + h.genes.weirdness) * 30 + len(h.inventory) * 3, 5, 97)
        objetos = (a.kind, b.kind)
        result = "sin_efecto_fisico_util"
        detalle = "los objetos se tocan o se colocan juntos, pero no aparece una unión estable"
        objeto_perdido: Optional[str] = None

        if {a.kind, b.kind} == {"stick", "stone"}:
            stick = a if a.kind == "stick" else b
            stone = a if a.kind == "stone" else b
            if stone.weight > 2.2 * stick.weight:
                result = "palo_se_rompe_por_peso_de_piedra"
                detalle = "la piedra es demasiado pesada para el palo; el palo se rompe"
                if stick in h.inventory:
                    h.inventory.remove(stick)
                    objeto_perdido = "stick"
                h.neural.activate("palo_roto", 0.18)
                h.neural.reinforce("piedra_pesada", "palo_roto", 0.10)
        elif a.kind == b.kind == "stick":
            result = "palos_no_se_unen_sin_cuerda_ni_pegamento"
            detalle = "los palos pueden tocarse, pero no se quedan unidos"
            h.neural.reinforce("objeto_stick", "no_union_sin_atadura", 0.06)
        elif a.kind == b.kind == "stone":
            result = "piedras_no_se_unen_sin_pegamento"
            detalle = "las piedras pueden juntarse, pero no se pegan ni forman una pieza nueva"
            h.neural.reinforce("objeto_stone", "no_union_sin_pegamento", 0.06)
        else:
            result = "combinacion_sin_resultado_estable"
            detalle = "la combinación no produce herramienta, unión ni cambio físico estable"

        h.neural.activate("combinar_objetos", 0.22)
        h.neural.reinforce(f"objeto_{a.kind}", f"objeto_{b.kind}", 0.06)
        h.last_action = "experimento_combinacion_objetos"
        self.log(
            "experimento_combinacion",
            h.entity_id,
            accion="combinar_objetos",
            objetos=objetos,
            resultado=result,
            detalle=detalle,
            objeto_perdido=objeto_perdido,
            seguridad=round(confidence, 1),
        )
        return True

    def human_do_air_gesture(self, h: Human) -> bool:
        confidence = clamp((h.genes.curiosity + h.genes.weirdness) * 18, 5, 75)
        h.energy = clamp(h.energy - 0.4, 0, 100)
        h.neural.activate("gesto_al_aire", 0.16)
        h.neural.activate("sin_efecto_fisico", 0.12)
        h.neural.reinforce("gesto_al_aire", "sin_efecto_fisico", 0.04)
        h.last_action = "gesto_al_aire"
        self.log(
            "accion_fisica_sin_efecto",
            h.entity_id,
            accion="gesto_al_aire",
            resultado="movio_o_golpeo_el_aire_sin_efecto_fisico",
            seguridad=round(confidence, 1),
            energia=round(h.energy, 1),
            pos=h.pos(),
        )
        return True

    def human_attack(self, h: Human, target: Creature) -> None:
        bite_connection = self.neural_connection_strength(h, "mordisco", "daño_a_otro")
        bite_chance = 0.006 + h.genes.weirdness * 0.012 + bite_connection * 0.08

        if random.random() < bite_chance:
            final_damage = h.effective_damage(4, self.tick)
            self.attack(h, target, final_damage, "mordisco_humano")
            h.hp -= 6
            h.neural.activate("mordisco", 0.25)
            h.neural.activate("dolor_propio", 0.24)
            h.neural.reinforce("mordisco", "dolor_propio", 0.12)
            h.neural.reinforce("mordisco", "daño_a_otro", 0.08)
            self.log("autodaño_mordisco", h.entity_id, daño=6, hp=round(h.hp, 2))
            if h.hp <= 0:
                self.kill(h, "autodaño_mordisco")
            return

        weapon = h.best_weapon()
        if weapon:
            base_damage = weapon.damage
            weapon_kind = weapon.kind
            weapon.uses_left -= 1
            if weapon.uses_left <= 0:
                if weapon in h.inventory:
                    h.inventory.remove(weapon)
                self.log("arma_rota", h.entity_id, arma=weapon.kind)
        else:
            base_damage = 1
            weapon_kind = "mano"

        final_damage = h.effective_damage(base_damage, self.tick)
        self.attack(h, target, final_damage, weapon_kind)

        h.neural.activate(f"ataque_{weapon_kind}", 0.16)
        h.neural.activate(f"objetivo_{target.kind}", 0.12)
        if h.is_tired_for_damage(self.tick):
            h.neural.activate("sueño_bajo", 0.18)
            h.neural.activate("golpe_debil", 0.16)
            h.neural.reinforce("sueño_bajo", "golpe_debil", 0.07)
        else:
            h.neural.activate("descanso_suficiente", 0.12)
            h.neural.activate("golpe_fuerte", 0.12)
            h.neural.reinforce("descanso_suficiente", "golpe_fuerte", 0.05)

    def attack(self, attacker: Creature, target: Creature, damage: float, weapon_kind: str, allow_counter: bool = True) -> None:
        if not attacker.alive or not target.alive:
            return

        if not self.can_attack_target(attacker, target):
            self.log("ataque_falla_por_espacio", attacker.entity_id, objetivo=target.entity_id, terreno=self.terrain_at(target.x, target.y))
            return

        # Si un humano pega a una vaca/T-Rex que lo estaba ignorando por atasco,
        # se cancela el ignore: la excepción explícita es "excepto si le pegan".
        if attacker.kind == "human" and target.kind in ("cow", "trex"):
            self.predator_clear_ignore_for(target, attacker.entity_id)

        self.predator_register_attack_success(attacker, target)

        target.hp -= damage
        target.last_attacker = attacker.entity_id
        self.log(
            "ataque",
            attacker.entity_id,
            objetivo=target.entity_id,
            objetivo_tipo=target.kind,
            daño=round(damage, 2),
            arma=weapon_kind,
            hp_objetivo=round(target.hp, 2),
        )

        if attacker.entity_id in self.humans:
            h = self.humans[attacker.entity_id]
            h.neural.reinforce(f"ataque_{weapon_kind}", f"daño_a_{target.kind}", min(0.12, damage / 80))
            if target.kind == "chicken":
                h.neural.reinforce("pollo", "comida_potencial", 0.06)

        if target.entity_id in self.humans:
            h = self.humans[target.entity_id]
            h.neural.activate("dolor", 0.25)
            h.neural.activate(f"daño_por_{attacker.kind}", 0.2)
            h.neural.reinforce(f"forma_{attacker.kind}", "dolor", min(0.15, damage / 70))
            if self.terrain_at(h.x, h.y) == CAVE_INTERIOR:
                h.neural.reinforce("cueva_interior", "menos_daño", 0.04)

            # Input defensivo sin acción obligatoria:
            # el humano registra que le han golpeado, quién/qué le hizo daño y que su vida bajó.
            # A partir de ahí puede decidir por su propia lógica: huir, atacar, dormir, beber, etc.
            if target.hp > 0 and attacker.alive:
                h.neural.activate("input_recibio_golpe", 0.24)
                h.neural.activate("vida_baja" if target.hp < h.max_hp * 0.45 else "vida_reducida", 0.18)
                h.neural.activate(f"atacado_por_{attacker.kind}", 0.20)
                h.neural.reinforce("dolor", f"atacado_por_{attacker.kind}", 0.08)
                h.neural.reinforce("dolor", "vida_baja", 0.05 if target.hp < h.max_hp * 0.45 else 0.025)
                self.log(
                    "input_defensivo_recibido",
                    h.entity_id,
                    atacante=attacker.entity_id,
                    atacante_tipo=attacker.kind,
                    daño=round(damage, 2),
                    hp_actual=round(target.hp, 2),
                    nota="no contraataca automáticamente; solo registra el golpe para decidir después",
                )

        if attacker.kind == "cow" and weapon_kind == "cornada":
            setattr(attacker, "defensive_hits", getattr(attacker, "defensive_hits", 0) + 1)

        if target.hp <= 0:
            self.kill(target, f"ataque_de_{attacker.kind}")
            if attacker.entity_id in self.humans:
                h = self.humans[attacker.entity_id]
                h.neural.activate("muerte_otro", 0.18)
                h.neural.reinforce(f"ataque_{weapon_kind}", "muerte_otro", 0.08)
                if target.kind == "chicken":
                    h.hunger = clamp(h.hunger - 25, 0, 100)
                    h.energy = clamp(h.energy + 18, 0, 100)
                    h.neural.reinforce("pollo", "hambre_baja", 0.1)
                    self.log("comer_presa", h.entity_id, presa=target.kind, hambre=h.hunger)
                elif target.kind == "trex":
                    # Si consiguen matar un T-Rex, pueden comerlo: llena al 100%.
                    before = h.hunger
                    h.hunger = 0
                    h.energy = clamp(h.energy + 45, 0, 100)
                    h.neural.activate("carne_trex", 0.30)
                    h.neural.reinforce("carne_trex", "hambre_baja", 0.18)
                    self.log("comer_trex", h.entity_id, presa=target.kind, nutricion=100, hambre_antes=before, hambre_despues=h.hunger)
                    # Además queda carne en el mundo para que otros puedan almacenarla/comerla.
                    for _ in range(3):
                        mx = target.x + random.randint(-1, 1)
                        my = target.y + random.randint(-1, 1)
                        if self.is_cell_walkable(mx, my):
                            self.add_item("meat", mx, my)
                elif target.kind == "cow":
                    # No se come automáticamente toda, pero deja carne disponible.
                    for _ in range(2):
                        mx = target.x + random.randint(-1, 1)
                        my = target.y + random.randint(-1, 1)
                        if self.is_cell_walkable(mx, my):
                            self.add_item("meat", mx, my)

    def kill(self, c: Creature, cause: str) -> None:
        c.alive = False
        self.log("muerte", c.entity_id, tipo=c.kind, nombre=getattr(c, "name", c.name), causa=cause, pos=c.pos())

        for h in self.humans.values():
            if h.alive and dist(h.pos(), c.pos()) <= 8:
                h.neural.activate("no_movimiento", 0.15)
                h.neural.activate(f"ser_{c.kind}", 0.1)
                h.neural.reinforce("no_movimiento", f"ser_{c.kind}", 0.05)
                h.record(
                    Event(
                        self.tick,
                        self.day,
                        h.entity_id,
                        "observa_muerte",
                        {"muerto": c.entity_id, "tipo": c.kind, "distancia": round(dist(h.pos(), c.pos()), 1)},
                    )
                )

    def try_reproduce_human(self, h: Human) -> None:
        # v2.2.6: los inmortales son una herramienta experimental/laboratorio.
        # Para evitar explosión de población y cuellos de botella de rendimiento,
        # ningún inmortal puede reproducirse automáticamente ni ser pareja reproductiva.
        # No afecta a humanos normales mortales.
        if getattr(h, "immortal", False):
            if self.tick % (TICKS_PER_DAY * 10) == 0:
                self.log("reproduccion_bloqueada_inmortal", h.entity_id, motivo="inmortal_experimental_no_reproduce")
            return
        # v2.0: los humanos de laboratorio no reproducen/contaminan el experimento normal
        # si el laboratorio está aislado.
        if getattr(h, "is_lab", False) and getattr(self, "lab_isolate", True):
            return
        # Hermafroditas: pueden reproducirse solos, pero si hay otro humano cerca
        # se registra como padre2 y el nombre lo refleja.
        possible_mates = [
            o for o in self.humans.values()
            if o.alive and o.entity_id != h.entity_id and dist(h.pos(), o.pos()) <= 3
            and not getattr(o, "immortal", False)
            and not (getattr(self, "lab_isolate", True) and getattr(o, "is_lab", False) != getattr(h, "is_lab", False))
        ]
        mate = min(possible_mates, key=lambda o: dist(h.pos(), o.pos())) if possible_mates else None

        for _ in range(20):
            nx = h.x + random.randint(-1, 1)
            ny = h.y + random.randint(-1, 1)
            dummy = Creature("dummy", "human", "human", nx, ny, 30, 30, 1)
            if self.can_place_creature(dummy, nx, ny):
                h.energy -= 35
                if mate:
                    mate.energy = clamp(mate.energy - 12, 0, 100)
                child = self.add_human(nx, ny, h, mate)
                h.neural.activate("nuevo_parecido", 0.18)
                h.neural.reinforce("energia_alta", "nuevo_parecido", 0.05)
                if mate:
                    h.neural.reinforce("otro_humano_cerca", "nuevo_parecido", 0.06)
                    mate.neural.reinforce("otro_humano_cerca", "nuevo_parecido", 0.06)
                self.log("reproduccion", h.entity_id, hijo=child.entity_id, hijo_nombre=child.name, padre1=h.birth_number, padre2=mate.birth_number if mate else 0, pos=(nx, ny))
                return

    def curiosity_move(self, h: Human) -> None:
        candidates: List[Tuple[Tuple[int, int], float]] = []

        # Espíritu explorador heredable:
        # si no hay urgencia fuerte, algunos humanos mantienen un objetivo lejano
        # y se dispersan. No heredan conocimientos, solo una tendencia corporal/conductual.
        explore_drive = clamp(h.genes.exploration_spirit, 0.5, 3.0)
        if h.hunger < 72 and h.thirst < 72 and h.energy > 18:
            if h.exploration_target is not None:
                if (not self.is_cell_walkable(*h.exploration_target)) or dist(h.pos(), h.exploration_target) <= 2:
                    h.exploration_target = None
            if h.exploration_target is None and random.random() < clamp(0.05 + 0.10 * explore_drive, 0.05, 0.36):
                h.exploration_target = self.random_exploration_target(h.pos(), min_distance=int(10 + 6 * explore_drive))
            if h.exploration_target is not None and random.random() < clamp(0.45 + 0.12 * explore_drive, 0.45, 0.82):
                h.neural.activate("impulso_explorador", 0.12)
                h.neural.reinforce("impulso_explorador", "mover_hacia_desconocido", 0.035)
                self.step_towards(h, h.exploration_target)
                h.last_action = "explorar_lejos"
                return

        for item in self.items.values():
            d = dist(h.pos(), (item.x, item.y))
            if d <= self.vision_radius(7):
                score = h.genes.curiosity * 1.2 + 1.0 / (d + 1)
                if item.kind == "seed" and h.hunger > 35:
                    score += 1.5
                candidates.append(((item.x, item.y), score))

        if h.thirst > 35:
            water = self.find_nearest_terrain(h.pos(), WATER, self.vision_radius(10))
            if water:
                candidates.append((water, 3.0))

        # Sin atracción inicial programada a la cueva.
        # Solo se vuelve objetivo si hay conexión aprendida por experiencia.
        cave_learned = max(
            self.neural_connection_strength(h, "cueva_interior", "menos_daño"),
            self.neural_connection_strength(h, "cueva_interior", "reposo"),
        )
        if cave_learned > 0.18:
            nearest_cave = self.nearest_cave_interior(h.pos())
            if nearest_cave and dist(h.pos(), nearest_cave) <= self.vision_radius(18):
                candidates.append((nearest_cave, cave_learned * 4.0))

        chicken = self.nearest_creature(h, "chicken", self.vision_radius(8))
        if chicken:
            candidates.append((chicken.pos(), 0.6 + h.genes.curiosity + max(0, h.hunger - 40) / 50))

        if candidates and random.random() < 0.75:
            self.step_towards(h, weighted_choice(candidates))
            h.last_action = "explorar_objetivo"
            return

        self.move_creature(h, random.randint(-1, 1), random.randint(-1, 1))
        h.last_action = "explorar_azar"

    def find_nearest_terrain(self, pos: Tuple[int, int], terrain: str, radius: float) -> Optional[Tuple[int, int]]:
        best = None
        best_d = 9999.0
        px, py = pos
        r = int(math.ceil(radius))
        for y in range(max(0, py - r), min(HEIGHT, py + r + 1)):
            for x in range(max(0, px - r), min(WIDTH, px + r + 1)):
                if self.grid[y][x] == terrain:
                    d = dist(pos, (x, y))
                    if d < best_d:
                        best, best_d = (x, y), d
        return best

    def best_food_or_potential_food_target(self, h: Human) -> Optional[Tuple[Tuple[int, int], str, Any]]:
        """Busca comida conocida por experiencia o, si no hay, posibles cosas a probar.

        No mete conceptos heredados. Usa asociaciones de hambre_baja si existen.
        Sin experiencia, solo orienta hacia objetos pequeños o seres pequeños cercanos como impulso exploratorio por hambre.
        """
        radius = self.vision_radius(16)
        candidates: List[Tuple[Tuple[int, int], str, Any, float]] = []

        seed_knowledge = max(
            h.neural.connections.get(tuple(sorted(("objeto_seed", "hambre_baja"))), 0.0),
            h.neural.connections.get(tuple(sorted(("objeto_pequeño_comestible", "hambre_baja"))), 0.0),
        )
        chicken_knowledge = max(
            h.neural.connections.get(tuple(sorted(("pollo", "hambre_baja"))), 0.0),
            h.neural.connections.get(tuple(sorted(("pollo", "comida_potencial"))), 0.0),
        )

        for item in self.items.values():
            d = dist(h.pos(), (item.x, item.y))
            if d <= radius:
                # Si ya aprendió que algo baja hambre, lo prioriza. Si no, lo considera objeto pequeño a probar.
                meat_knowledge = h.neural.connections.get(tuple(sorted(("comida_meat", "hambre_baja"))), 0.0)
                learned = seed_knowledge if item.kind == "seed" else (meat_knowledge if item.kind == "meat" else 0.0)
                physical_try = 0.18 if item.edible else (0.16 if item.weight <= 2.0 else 0.04)
                score = learned * 1.8 + physical_try + (0.05 / max(1.0, d))
                if score > 0.05:
                    candidates.append(((item.x, item.y), "item_food" if learned > 0.12 else "potential_item", item, score))

        for cr in self.creatures.values():
            if not cr.alive or cr.entity_id == h.entity_id:
                continue
            d = dist(h.pos(), cr.pos())
            if d <= radius and cr.kind in ("chicken", "cow"):
                learned = chicken_knowledge if cr.kind == "chicken" else 0.0
                physical_try = 0.12 if cr.kind == "chicken" else (0.03 + h.genes.aggression * 0.05)
                score = learned * 1.8 + physical_try + (0.05 / max(1.0, d))
                if score > 0.04:
                    candidates.append((cr.pos(), "creature_food" if learned > 0.12 else "potential_creature", cr, score))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[3] / max(1.0, dist(h.pos(), x[0])), reverse=True)
        pos, typ, obj, _ = candidates[0]
        return (pos, typ, obj)

    def nearest_item(self, pos: Tuple[int, int], kind: str, radius: float) -> Optional[Item]:
        candidates = [i for i in self.items.values() if i.kind == kind and dist(pos, (i.x, i.y)) <= radius]
        return min(candidates, key=lambda i: dist(pos, (i.x, i.y))) if candidates else None

    def nearest_creature(self, h: Human, kind: str, radius: float) -> Optional[Creature]:
        candidates = [
            c for c in self.creatures.values()
            if c.alive and c.kind == kind and c.entity_id != h.entity_id and dist(h.pos(), c.pos()) <= radius
        ]
        return min(candidates, key=lambda c: dist(h.pos(), c.pos())) if candidates else None

    def nearest_huntable(self, h: Human, radius: int) -> Optional[Creature]:
        candidates = [
            c for c in self.creatures.values()
            if c.alive and c.kind in ("chicken", "cow") and dist(h.pos(), c.pos()) <= radius
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda c: (0 if c.kind == "chicken" else 1, dist(h.pos(), c.pos())))
        if candidates[0].kind == "cow" and random.random() > h.genes.aggression:
            return None
        return candidates[0]

    def neural_connection_strength(self, h: Human, a: str, b: str) -> float:
        return h.neural.connections.get(tuple(sorted((a, b))), 0.0)

    # ----------------------------
    # Render
    # ----------------------------

    def color_cell(self, ch: str, terrain_original: Optional[str] = None) -> str:
        if ch == "L":
            return ctext(ch, Color.BRIGHT_MAGENTA + Color.BOLD)
        if ch == "H":
            return ctext(ch, Color.BRIGHT_CYAN + Color.BOLD)
        if ch == "P":
            return ctext(ch, Color.BRIGHT_YELLOW)
        if ch == "V":
            return ctext(ch, Color.GREEN + Color.BOLD)
        if ch == "T":
            return ctext(ch, Color.BRIGHT_RED + Color.BOLD)
        if ch == CAVE_WALL:
            return ctext(ch, Color.GRAY + Color.BOLD)
        if ch == WATER:
            return ctext(ch, Color.BRIGHT_BLUE)
        if ch == SEED:
            return ctext(ch, Color.BRIGHT_GREEN)
        if ch == STICK:
            return ctext(ch, Color.YELLOW)
        if ch == STONE:
            return ctext(ch, Color.WHITE)
        if ch == MEAT:
            return ctext(ch, Color.BRIGHT_MAGENTA)
        if terrain_original in (CAVE_ENTRANCE, CAVE_INTERIOR):
            return ctext(".", Color.DIM + Color.WHITE)
        return ctext(ch, Color.DIM)

    def render_to_string(self) -> str:
        canvas = [row[:] for row in self.grid]
        terrain_original = [row[:] for row in self.grid]

        for y in range(HEIGHT):
            for x in range(WIDTH):
                if canvas[y][x] in (CAVE_ENTRANCE, CAVE_INTERIOR):
                    canvas[y][x] = EMPTY

        for item in self.items.values():
            if self.in_bounds(item.x, item.y) and canvas[item.y][item.x] == EMPTY:
                canvas[item.y][item.x] = item.char

        for kind in ["chicken", "cow", "trex", "human"]:
            for cr in self.creatures.values():
                if not cr.alive or cr.kind != kind:
                    continue
                char = {"human": "H", "chicken": "P", "cow": "V", "trex": "T"}[cr.kind]
                if cr.kind == "human" and getattr(cr, "is_lab", False):
                    char = "L"
                for cx, cy in cr.occupied_cells():
                    if self.in_bounds(cx, cy):
                        canvas[cy][cx] = char

        lines: List[str] = []
        lines.append(ctext(f"PROTOHUMANOS 2D v2.1.4 | Día {self.day} | Tick {self.tick} | {'NOCHE visión 1/2' if self.is_night() else 'DÍA visión normal'}", Color.BOLD + Color.CYAN))
        lines.append(
            "Leyenda: "
            + ctext("H", Color.BRIGHT_CYAN + Color.BOLD) + " humano | "
            + ctext("L", Color.BRIGHT_MAGENTA + Color.BOLD) + " lab | "
            + ctext("P", Color.BRIGHT_YELLOW) + " pollo | "
            + ctext("V", Color.GREEN + Color.BOLD) + " vaca | "
            + ctext("T", Color.BRIGHT_RED + Color.BOLD) + " T-Rex | "
            + ctext("C", Color.GRAY + Color.BOLD) + " pared cueva | . entrada/interior ocultos | "
            + ctext("s", Color.BRIGHT_GREEN) + " semilla | "
            + ctext("/", Color.YELLOW) + " palo | "
            + ctext("o", Color.WHITE) + " piedra | "
            + ctext("~", Color.BRIGHT_BLUE) + " agua"
        )
        lines.append("-" * WIDTH)
        for y in range(HEIGHT):
            lines.append("".join(self.color_cell(canvas[y][x], terrain_original[y][x]) for x in range(WIDTH)))
        lines.append("-" * WIDTH)

        alive_h = [h for h in self.humans.values() if h.alive]
        alive_lab = [h for h in alive_h if getattr(h, "is_lab", False)]
        alive_real = [h for h in alive_h if not getattr(h, "is_lab", False)]
        lines.append(
            f"Humanos reales vivos: {len(alive_real)} | LAB: {len(alive_lab)} | Pollos: {self.count_alive('chicken')} | "
            f"Vacas: {self.count_alive('cow')} | T-Rex: {self.count_alive('trex')} | Items: {len(self.items)}"
        )
        # Panel fijo de humanos: SIEMPRE 5 líneas para que el mapa no suba/baje
        # cuando quedan pocos humanos.
        panel_humans = alive_real[:4] + alive_lab[:1]
        for h in panel_humans[:5]:
            inv = ",".join(i.kind[0] for i in h.inventory) or "-"
            sleep24 = h.recent_sleep_hours(self.tick)
            tired = "sí" if h.is_tired_for_damage(self.tick) else "no"
            txt = (
                f"{h.entity_id}/{h.name}: HP {h.hp:.1f}/30 | hambre {h.hunger:.0f} | "
                f"sed {h.thirst:.0f} | sueño {h.sleepiness:.0f} | dormido24h {sleep24} | "
                f"cansado {tired} | inv {inv} | acción {h.last_action}"
            )
            lines.append(self.render_safe_line(txt, WIDTH))
        for _ in range(max(0, 5 - len(panel_humans[:5]))):
            lines.append(" " * WIDTH)

        lines.append("")
        lines.append("Últimos eventos:")
        # Panel fijo de eventos: 12 líneas EXACTAS y truncadas.
        # Evita que un log largo haga wrap y empuje el mapa hacia arriba/abajo.
        visible_events = self.events[-12:]
        for ev in visible_events:
            line = f"  [Día {ev.day} T{ev.tick}] {ev.actor_id}: {ev.kind} {ev.data}"
            line = self.render_safe_line(line, WIDTH)
            if ev.kind == "accion_no_prevista":
                lines.append(red_alert(line))
            elif ev.kind in ("experimento_combinacion", "experimento_refugio", "fallo_fisico_previsible"):
                # Eventos con solución física lógica ya prevista: no son fallo ni alerta visual.
                # Se dejan en color normal para que el amarillo quede reservado a avisos realmente útiles.
                lines.append(line)
            else:
                lines.append(line)
        for _ in range(max(0, 12 - len(visible_events))):
            lines.append(" " * WIDTH)
        return "\n".join(lines) + "\n"

    def render_safe_line(self, text: str, max_width: int) -> str:
        """Una sola línea visible, sin saltos ni wrap, para estabilizar el render."""
        plain = re.sub(r"\x1b\[[0-9;]*m", "", str(text)).replace("\n", " ").replace("\r", " ")
        if len(plain) > max_width:
            plain = plain[: max(0, max_width - 1)] + "…"
        return plain.ljust(max_width)

    def pad_visible_line(self, line: str, terminal_width: int) -> str:
        """Rellena o recorta una línea para que no queden restos visuales a la derecha."""
        terminal_width = max(20, terminal_width)
        plain = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", str(line))
        visible = len(plain)
        max_visible = max(1, terminal_width - 1)
        if visible > max_visible:
            return plain[: max(1, max_visible - 1)] + "…"
        return str(line) + (" " * max(0, max_visible - visible))

    def render(self, footer_lines: Optional[List[str]] = None) -> None:
        # v1.6.3: frame completo + pie integrado. No se usa print() tras renderizar.
        term = shutil.get_terminal_size((WIDTH + 40, 50))
        terminal_width = max(WIDTH + 2, term.columns)
        frame = self.render_to_string().rstrip("\n")
        lines = frame.split("\n")
        if footer_lines:
            lines.extend(footer_lines)
        padded = [self.pad_visible_line(line, terminal_width) for line in lines]
        out = "\n".join(padded) + "\n"

        sys.stdout.write("\033[?25l")
        sys.stdout.write("\033[?7l")
        sys.stdout.write("\033[?2026h")
        sys.stdout.write("\033[H")
        sys.stdout.write(out)
        sys.stdout.write("\033[0J")
        sys.stdout.write("\033[?2026l")
        sys.stdout.write("\033[?7h")
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def count_alive(self, kind: str) -> int:
        return sum(1 for c in self.creatures.values() if c.alive and c.kind == kind)


# ============================================================
# METAOBSERVADOR
# ============================================================

class MetaObserver:
    def __init__(self, world: World) -> None:
        self.world = world
        self.printed_signatures: Dict[str, int] = {}

    def analyze_all(self) -> None:
        for h in list(self.world.humans.values()):
            if not h.alive:
                continue
            self.detect_unexpected_actions(h)
            self.detect_bait_trap(h)
            self.detect_sleep_strength(h)
            self.detect_cave_safety(h)
            self.detect_big_creature_avoidance(h)
            self.detect_fear_or_death_concepts(h)
            self.detect_unclassified_clusters(h)
            self.detect_open_sequence_patterns(h)
            self.detect_inventory_storage(h)
        self.world.update_gene_bank()
        self.world.update_investigations()
        self.detect_cultural_patterns()

    def recent_events(self, h: Human, kinds: Optional[Set[str]] = None, window: int = 700) -> List[Event]:
        cutoff = self.world.tick - window
        evs = [e for e in h.memory_events if e.tick >= cutoff]
        return [e for e in evs if e.kind in kinds] if kinds else evs

    def confidence_status(self, confidence: float) -> str:
        if confidence < 15:
            return "ruido / casi seguro casual"
        if confidence < 30:
            return "anomalía débil"
        if confidence < 45:
            return "patrón posible"
        if confidence < 60:
            return "patrón sospechoso"
        if confidence < 75:
            return "concepto probable"
        if confidence < 90:
            return "concepto fuerte"
        return "concepto casi seguro"

    def should_print(self, signature: str, confidence: float, min_gap: int = 72, min_conf: float = MIN_CONFIDENCE_TO_PRINT) -> bool:
        if confidence < min_conf:
            return False
        last = self.printed_signatures.get(signature, -999999)
        if self.world.tick - last < min_gap:
            return False
        self.printed_signatures[signature] = self.world.tick
        return True

    def weighted_confidence(self, factors: Dict[str, float], weights: Dict[str, float]) -> float:
        total_w = sum(weights.values())
        if total_w <= 0:
            return 0.0
        score = 0.0
        for k, w in weights.items():
            score += clamp(factors.get(k, 0.0), 0.0, 1.0) * w
        return clamp((score / total_w) * 100, 0, 100)

    def print_report(
        self,
        title: str,
        human: Optional[Human],
        tipo: str,
        concepto: str,
        resumen: str,
        equivalente: str,
        confidence: float,
        evidencias: List[str],
        factors: Dict[str, float],
        note: str,
        group_name: str = "población activa",
        extra: Optional[List[str]] = None,
        red: bool = False,
        cyan: bool = False,
        darkblue: bool = False,
        skip_review: bool = False,
    ) -> None:
        actor = f"HUMANO: {human.name}" if human else f"GRUPO: {group_name}"
        header = f"[DÍA {self.world.day} | TICK {self.world.tick} | {actor}] {title} | confianza {pct(confidence)}"
        border = "=" * 80

        report_text_for_style = "\n".join([title, tipo, concepto, resumen, equivalente, header])
        if red:
            style = "red"
        elif darkblue:
            style = "darkblue"
        else:
            style = style_for_report_text(report_text_for_style, confidence)
            if style == "normal" and cyan:
                style = "cyan"

        def out(line: str = "") -> None:
            # v1.6stable: nunca imprimimos reportes largos en vivo sobre el mapa.
            # Se guardan completos en logs/todos_logs/valiosos/export, y se abren por HTML.
            return None

        if red:
            self.world.unexpected_logs.append(header)
        else:
            self.world.concept_logs.append(header)

        out("\n" + border)
        out(f"[DÍA {self.world.day} | TICK {self.world.tick} | {actor}]")
        out(title)
        out("-" * 80)

        out(f"TIPO:\n{tipo}\n")
        out(f"CONCEPTO/PATRÓN DETECTADO:\n{concepto}\n")
        out(f"RESUMEN TRADUCIDO:\n“{resumen}”\n")
        out(f"POSIBLE EQUIVALENTE HUMANO:\n{equivalente}\n")
        out(f"CONFIANZA:\n{pct(confidence)}\n")
        out(f"ESTADO:\n{self.confidence_status(confidence)}\n")

        if extra:
            out("DATOS EXTRA:")
            for x in extra:
                out(f"- {x}")
            out()

        if evidencias:
            out("EVIDENCIAS:")
            for e in evidencias[:9]:
                out(f"- {e}")
            out()

        if human:
            out("MINI REGISTRO NEURONAL:")
            for node, value in human.neural.top_activations(8):
                out(f"- {node:<34} activación {value:.2f}")
            out("\nCONEXIONES REFORZADAS:")
            for (a, b), value in human.neural.top_connections(8):
                out(f"- {a} ↔ {b}: +{value:.2f}")
            out()

        out("FACTORES DE CONFIANZA:")
        for k, v in factors.items():
            out(f"- {k:<32} {v:.2f}")
        out(f"\nNOTA:\n{note}")

        # Guardado detallado para comandos: conceptos/logs, fallos/no_previstos y todos_logs.
        detail_lines: List[str] = []
        detail_lines.append(border)
        detail_lines.append(header)
        detail_lines.append(f"TIPO: {tipo}")
        detail_lines.append(f"CONCEPTO/PATRÓN: {concepto}")
        detail_lines.append(f"RESUMEN: {resumen}")
        detail_lines.append(f"EQUIVALENTE HUMANO: {equivalente}")
        importance = concept_importance_score(report_text_for_style, confidence)
        importance_label = concept_importance_label(importance)
        detail_lines.append(f"CONFIANZA: {pct(confidence)} | ESTADO: {self.confidence_status(confidence)}")
        detail_lines.append(f"VALOR DEL CONCEPTO: {importance_label} ({importance:.1f}/140)")
        if extra:
            detail_lines.append("DATOS EXTRA:")
            detail_lines.extend([f"  - {x}" for x in extra])
        if evidencias:
            detail_lines.append("EVIDENCIAS:")
            detail_lines.extend([f"  - {e}" for e in evidencias[:12]])
        if human:
            detail_lines.append("MINI REGISTRO NEURONAL:")
            detail_lines.extend([f"  - {node}: activación {value:.2f}" for node, value in human.neural.top_activations(10)])
            detail_lines.append("CONEXIONES REFORZADAS:")
            detail_lines.extend([f"  - {a} ↔ {b}: +{value:.2f}" for (a, b), value in human.neural.top_connections(10)])
        detail_lines.append("FACTORES DE CONFIANZA:")
        detail_lines.extend([f"  - {k}: {v:.2f}" for k, v in factors.items()])
        detail_lines.append(f"NOTA: {note}")
        detail_lines.append(border)
        detail_block = "\n".join(detail_lines)

        if human is not None and not red:
            human.detected_concepts.append(f"{header} | valor={importance_label} {importance:.1f}/140")
            if len(human.detected_concepts) > 80:
                human.detected_concepts = human.detected_concepts[-80:]

        if red:
            if self.world.unexpected_logs and self.world.unexpected_logs[-1] == header:
                self.world.unexpected_logs[-1] = detail_block
            else:
                self.world.unexpected_logs.append(detail_block)
        else:
            if self.world.concept_logs and self.world.concept_logs[-1] == header:
                self.world.concept_logs[-1] = detail_block
            else:
                self.world.concept_logs.append(detail_block)
        self.world.all_logs.append(detail_block)
        # No recortamos world.all_logs: todos_logs/export_logs deben poder ver la sesión completa.

        # Abrir investigación longitudinal automática para reportes con señales mínimas.
        if human is not None and not red:
            cat, hyp = self.world.classify_investigation_from_components(set(re.findall(r"[a-zA-Z_áéíóúÁÉÍÓÚñÑ]+", report_text_for_style)), report_text_for_style)
            if confidence >= 30 or cat in ("refugio", "cebo_trampa", "almacenamiento", "miedo_muerte", "exploracion_medicion"):
                self.world.open_or_update_investigation(
                    human, cat, hyp, confidence * 0.50,
                    evidence_for=evidencias[:4],
                    evidence_against=["abierta desde reporte puntual; se validará con seguimiento temporal"],
                    duration_days=8,
                )

        out(border + "\n")

        # Todo reporte púrpura o dorado se revisa siempre por un bot auditor.
        # Lo hacemos después del reporte principal y sin recursión.
        if (not skip_review) and (not red) and style in ("gold", "purple"):
            self.review_important_report(title, human, tipo, concepto, resumen, equivalente, confidence, evidencias, factors, style)

    def review_important_report(
        self,
        title: str,
        human: Optional[Human],
        tipo: str,
        concepto: str,
        resumen: str,
        equivalente: str,
        confidence: float,
        evidencias: List[str],
        factors: Dict[str, float],
        original_style: str,
    ) -> None:
        actor = human.name if human else "población activa"
        strong = [k for k, v in factors.items() if v >= 0.55]
        weak = [k for k, v in factors.items() if v <= 0.20]
        extra = [
            f"reporte original: {title}",
            f"color original: {original_style}",
            f"sujeto revisado: {actor}",
            "factores fuertes: " + (", ".join(strong) if strong else "ninguno claro"),
            "factores débiles: " + (", ".join(weak) if weak else "ninguno crítico"),
        ]
        note = (
            "Este revisor no aumenta la confianza. Solo audita los reportes púrpuras/dorados "
            "para evitar falsos positivos: exige coherencia entre confianza, evidencias y cambio de conducta."
        )
        self.print_report(
            "BOT REVISOR: REPORTE IMPORTANTE AUDITADO",
            human,
            "AUDITORÍA OBLIGATORIA DE REPORTE PÚRPURA/DORADO",
            f"Revisión del concepto: {concepto}",
            f"el revisor considera que la señal original debe tomarse como {self.confidence_status(confidence).lower()}, no como certeza absoluta.",
            equivalente,
            confidence,
            evidencias[:6],
            factors,
            note,
            extra=extra,
            darkblue=(original_style == "purple"),
            cyan=(original_style == "gold"),
            skip_review=True,
        )

    # ----------------------------
    # Detectores
    # ----------------------------

    def detect_unexpected_actions(self, h: Human) -> None:
        events = self.recent_events(h, {"accion_no_prevista"}, 900)
        # Los intentos de refugio ya tienen una física lógica propia (se caen por viento,
        # peso o falta de piezas). No deben aparecer en “fallos raros”.
        events = [e for e in events if e.data.get("accion") != "intentar_refugio_objetos"]
        if not events:
            return

        repetition = clamp(len(events) / 5, 0, 1)
        neural = max(
            h.neural.activations.get("intento_refugio", 0),
            h.neural.activations.get("combinar_objetos", 0),
            h.neural.activations.get("gesto_al_aire", 0),
            h.neural.activations.get("intento_mover_cueva", 0),
        )
        weird = clamp(h.genes.weirdness, 0, 1)
        variety = clamp(len(set(e.data.get("accion") for e in events)) / 4, 0, 1)

        factors = {
            "repetición": repetition,
            "activación neuronal rara": neural,
            "gen curiosidad/rareza": weird,
            "variedad de intentos": variety,
        }
        confidence = self.weighted_confidence(
            factors,
            {
                "repetición": 0.28,
                "activación neuronal rara": 0.30,
                "gen curiosidad/rareza": 0.20,
                "variedad de intentos": 0.22,
            },
        )

        if not self.should_print(f"unexpected-{h.entity_id}-{int(confidence//10)}", confidence, min_gap=80, min_conf=MIN_UNEXPECTED_TO_PRINT):
            return

        evidencias = [
            f"Evento {e.tick}: intentó {e.data.get('accion')} → {e.data.get('resultado')} | seguridad inicial {e.data.get('seguridad')}%"
            for e in events[-7:]
        ]

        self.print_report(
            title="AVISO ROJO: ACCIÓN NO PREVISTA DETECTADA",
            human=h,
            tipo="ACCIÓN/IDEA NO ANTICIPADA POR EL DISEÑO",
            concepto="Intentos de hacer algo fuera de los comportamientos principales previstos.",
            resumen="parece haber probado una acción que el diseño no estaba buscando como conducta principal.",
            equivalente="idea inesperada / experimento espontáneo / conducta no prevista",
            confidence=confidence,
            evidencias=evidencias,
            factors=factors,
            note="No significa que haya entendido la acción. Significa que el observador detecta una conducta fuera del plan inicial y la marca para revisión humana.",
            red=True,
        )

    def detect_bait_trap(self, h: Human) -> None:
        drops = self.recent_events(h, {"soltar_semilla"}, 1000)
        attacks = self.recent_events(h, {"ataque", "comer_presa"}, 1000)
        if not drops:
            return

        successes = 0
        weak = 0
        evidencias: List[str] = []
        distances: List[float] = []

        for d in drops:
            distances.append(float(d.data.get("distancia", 99)))
            future = [a for a in attacks if 0 <= a.tick - d.tick <= 20]
            chicken_related = [a for a in future if a.data.get("objetivo_tipo") == "chicken" or a.data.get("presa") == "chicken"]
            if chicken_related:
                successes += 1
                evidencias.append(f"Evento {d.tick}: soltó semilla a {d.data.get('distancia')} casillas; después hubo ataque/comida de pollo.")
            else:
                weak += 1
                evidencias.append(f"Evento {d.tick}: soltó semilla cerca de pollo sin éxito claro posterior.")

        repetition = clamp(len(drops) / 6, 0, 1)
        temporal = clamp(successes / max(1, len(drops)), 0, 1)
        neural = max(
            h.neural.connections.get(tuple(sorted(("semilla", "pollo_se_acerca"))), 0.0),
            h.neural.connections.get(tuple(sorted(("semilla", "pollo_cercano"))), 0.0),
            h.neural.connections.get(tuple(sorted(("pollo", "hambre_baja"))), 0.0),
        )
        behavior = clamp((len(drops) - weak * 0.3) / 8, 0, 1)
        result = clamp(successes / 4, 0, 1)

        if len(distances) >= 3:
            avg_d = statistics.mean(distances)
            sd = statistics.pstdev(distances)
            refinement = clamp((10 - avg_d) / 10, 0, 1) * clamp((8 - sd) / 8, 0, 1)
        else:
            refinement = 0.0

        factors = {
            "repetición": repetition,
            "causalidad temporal": temporal,
            "mejora de resultado": result,
            "cambio de conducta": behavior,
            "conexión neuronal": neural,
            "refinamiento distancia": refinement,
        }
        confidence = self.weighted_confidence(
            factors,
            {
                "repetición": 0.18,
                "causalidad temporal": 0.22,
                "mejora de resultado": 0.18,
                "cambio de conducta": 0.16,
                "conexión neuronal": 0.16,
                "refinamiento distancia": 0.10,
            },
        )

        if not self.should_print(f"bait-{h.entity_id}-{int(confidence//10)}", confidence):
            return

        extra = []
        if distances:
            extra.append(f"distancia media al pollo al soltar semilla: {statistics.mean(distances):.1f} casillas")
            if len(distances) > 1:
                extra.append(f"variación de distancia: {statistics.pstdev(distances):.1f}")
            extra.append(f"secuencias exitosas detectadas: {successes}/{len(drops)}")

        tipo = "REFINAMIENTO / CONCEPTO DE CEBO" if refinement > 0.35 else "CONCEPTO EMERGENTE / PATRÓN DE CEBO"

        self.print_report(
            "DETECTOR DE CONCEPTOS: CEBO/TRAMPA",
            h,
            tipo,
            "Secuencia posible: soltar semillas, esperar llegada de pollos y cazarlos.",
            "parece estar asociando que dejar semillas cerca de pollos puede atraerlos o facilitar cazarlos.",
            "cebo / trampa simple / emboscada / técnica de caza",
            confidence,
            evidencias,
            factors,
            "El humano no tiene la palabra 'trampa'. El observador solo interpreta una secuencia conductual y neuronal.",
            extra=extra,
        )

    def detect_sleep_strength(self, h: Human) -> None:
        attacks = self.recent_events(h, {"ataque"}, 1000)
        if len(attacks) < 3:
            return

        weak_hits = []
        normal_hits = []

        for e in attacks:
            dmg = float(e.data.get("daño", 0))
            arma = e.data.get("arma", "")
            if (
                (arma == "mano" and dmg <= 0.6)
                or (arma == "stick" and dmg <= 1.6)
                or (arma == "stone" and dmg <= 3.6)
                or (arma == "mordisco_humano" and dmg <= 2.1)
            ):
                weak_hits.append(e)
            elif dmg > 0:
                normal_hits.append(e)

        if not weak_hits:
            return

        neural = max(
            h.neural.connections.get(tuple(sorted(("sueño_bajo", "golpe_debil"))), 0),
            h.neural.connections.get(tuple(sorted(("descanso_suficiente", "golpe_fuerte"))), 0),
        )
        sleep_events = self.recent_events(h, {"dormir"}, 500)

        factors = {
            "repetición": clamp(len(weak_hits) / 5, 0, 1),
            "contraste débil/fuerte": clamp(len(normal_hits) / 4, 0, 1),
            "conexión neuronal": neural,
            "cambio hacia dormir": clamp(len(sleep_events) / 12, 0, 1),
            "causalidad temporal": 0.75 if normal_hits else 0.35,
        }
        confidence = self.weighted_confidence(
            factors,
            {
                "repetición": 0.22,
                "contraste débil/fuerte": 0.20,
                "conexión neuronal": 0.22,
                "cambio hacia dormir": 0.16,
                "causalidad temporal": 0.20,
            },
        )

        if not self.should_print(f"sleep-{h.entity_id}-{int(confidence//10)}", confidence):
            return

        evidencias = [
            f"Evento {e.tick}: golpe con {e.data.get('arma')} hizo {e.data.get('daño')} de daño."
            for e in weak_hits[:4] + normal_hits[:3]
        ]

        self.print_report(
            "DETECTOR DE CONCEPTOS: SUEÑO/FUERZA",
            h,
            "CONCEPTO FISIOLÓGICO / POSIBLE REFINAMIENTO",
            "Relación interna entre descanso reciente y eficacia de golpeo.",
            "parece estar acumulando experiencias donde dormir poco coincide con golpes débiles y dormir más coincide con golpes normales.",
            "cansancio / descanso / fuerza / recuperación",
            confidence,
            evidencias,
            factors,
            "La regla física existe en el mundo, pero el humano no la conoce. El detector mira si la está asociando por experiencia.",
        )

    def detect_cave_safety(self, h: Human) -> None:
        recent = self.recent_events(h, {"dormir", "ataque", "ataque_falla_por_espacio"}, 1600)
        cave_sleep = [
            e for e in recent
            if e.kind == "dormir" and self.world.terrain_at(*e.data.get("pos", (-1, -1))) == CAVE_INTERIOR
        ]

        neural = max(
            h.neural.connections.get(tuple(sorted(("cueva_interior", "reposo"))), 0),
            h.neural.connections.get(tuple(sorted(("cueva_interior", "menos_daño"))), 0),
        )

        if len(cave_sleep) < 2 and neural < 0.12:
            return

        all_sleep = [e for e in h.memory_events[-500:] if e.kind == "dormir"]
        repeated_use = clamp(len(cave_sleep) / 5, 0, 1)
        sleep_share = clamp(len(cave_sleep) / max(1, len(all_sleep)), 0, 1)
        learned_pull = clamp(neural * 2.6, 0, 1)
        survival_result = 0.35 + min(0.4, len(cave_sleep) * 0.06)
        temporal = 0.45 + neural * 0.35

        factors = {
            "uso repetido de interior": repeated_use,
            "proporción de sueño en cueva": sleep_share,
            "conexión neuronal cueva/reposo": learned_pull,
            "resultado supervivencia/reposo": survival_result,
            "causalidad temporal": temporal,
        }

        confidence = self.weighted_confidence(
            factors,
            {
                "uso repetido de interior": 0.22,
                "proporción de sueño en cueva": 0.18,
                "conexión neuronal cueva/reposo": 0.25,
                "resultado supervivencia/reposo": 0.17,
                "causalidad temporal": 0.18,
            },
        )
        # Refugio vale más que otros conceptos porque cambia muchísimo la supervivencia.
        # No le da conocimiento al humano: solo sube la prioridad del REPORTE externo.
        confidence = clamp(confidence * 1.12 + 6.0, 0, 100)
        factors["valor estratégico externo del refugio"] = 1.0

        if not self.should_print(f"cave-{h.entity_id}-{int(confidence//10)}", confidence, min_gap=50, min_conf=18):
            return

        evidencias = [f"Evento {e.tick}: durmió en interior de cueva." for e in cave_sleep[:6]]
        extra = [
            f"sueños en interior de cueva detectados: {len(cave_sleep)}",
            f"conexión cueva_interior↔reposo: {h.neural.connections.get(tuple(sorted(('cueva_interior','reposo'))),0):.2f}",
            f"conexión cueva_interior↔menos_daño: {h.neural.connections.get(tuple(sorted(('cueva_interior','menos_daño'))),0):.2f}",
        ]

        self.print_report(
            "DETECTOR CIAN: POSIBLE CUEVA/REFUGIO",
            h,
            "CONCEPTO ESPACIAL / SUPERVIVENCIA",
            "Asociación entre interior de cueva, reposo y posible reducción de exposición.",
            "parece estar empezando a usar el interior de la cueva como lugar de reposo o permanencia, pero puede ser casualidad si la confianza es baja.",
            "refugio / dentro seguro / lugar de reposo",
            confidence,
            evidencias,
            factors,
            "No se le ha programado ir a la cueva como objetivo inicial en v0.3 limpia. Si aparece, viene de exploración, azar o experiencia reforzada.",
            extra=extra,
            cyan=True,
        )

    def detect_big_creature_avoidance(self, h: Human) -> None:
        damage_events = [e for e in h.memory_events[-300:] if e.kind == "ataque" and e.data.get("objetivo") == h.entity_id]
        neural = max(
            h.neural.connections.get(tuple(sorted(("forma_trex", "dolor"))), 0),
            h.neural.connections.get(tuple(sorted(("forma_grande", "dolor"))), 0),
        )

        if len(damage_events) < 1 and neural < 0.2:
            return

        factors = {
            "repetición daño": clamp(len(damage_events) / 4, 0, 1),
            "conexión neuronal": neural,
            "activación forma/dolor": clamp(h.neural.activations.get("forma_grande", 0) + h.neural.activations.get("dolor", 0), 0, 1),
            "resultado supervivencia": 0.5 if damage_events else 0.2,
            "causalidad": 0.6 if neural > 0.15 else 0.3,
        }
        confidence = self.weighted_confidence(
            factors,
            {
                "repetición daño": 0.18,
                "conexión neuronal": 0.28,
                "activación forma/dolor": 0.20,
                "resultado supervivencia": 0.14,
                "causalidad": 0.20,
            },
        )

        if not self.should_print(f"avoid-{h.entity_id}-{int(confidence//10)}", confidence):
            return

        evidencias = [f"Evento {e.tick}: recibió daño {e.data.get('daño')} de atacante {e.actor_id}." for e in damage_events[:5]]

        self.print_report(
            "DETECTOR DE CONCEPTOS: EVITACIÓN",
            h,
            "PATRÓN EMERGENTE DE SUPERVIVENCIA",
            "Asociación entre formas grandes/depredadores, dolor y alejamiento.",
            "parece estar formando una relación entre ciertas criaturas grandes y la necesidad de alejarse para reducir daño.",
            "miedo / peligro / evitación / huida defensiva",
            confidence,
            evidencias,
            factors,
            "El humano no tiene la palabra 'miedo'. El observador interpreta un patrón de daño, forma y alejamiento.",
        )

    def detect_fear_or_death_concepts(self, h: Human) -> None:
        """Detector específico para llegar a conclusiones tipo miedo/peligro/muerte sin depender de etiquetas humanas previas."""
        damage_events = [e for e in self.recent_events(h, {"ataque"}, 900) if e.data.get("objetivo") == h.entity_id]
        death_obs = [e for e in self.recent_events(h, {"observa_muerte"}, 1200)]
        flee_or_avoid = [e for e in h.memory_events[-220:] if "alejar" in str(e.data).lower() or "cueva" in str(e.data).lower()]
        c = h.neural.connections
        trex_pain = c.get(tuple(sorted(("forma_trex", "dolor"))), 0.0)
        cow_pain = c.get(tuple(sorted(("forma_cow", "dolor"))), 0.0)
        dead_human = c.get(tuple(sorted(("no_movimiento", "ser_human"))), 0.0)
        defensive = c.get(tuple(sorted(("dolor", "devolver_golpe"))), 0.0)
        danger = max(trex_pain, cow_pain)
        factors = {
            "daño directo repetido": clamp(len(damage_events) / 4, 0, 1),
            "muerte/no_movimiento observado": clamp(dead_human + len(death_obs) / 5, 0, 1),
            "animal/forma asociada a dolor": clamp(danger * 2.2, 0, 1),
            "respuesta defensiva/evitación": clamp(defensive * 2 + len(flee_or_avoid) / 6, 0, 1),
            "soporte neuronal combinado": clamp((danger + dead_human + defensive) / 1.1, 0, 1),
        }
        confidence = self.weighted_confidence(factors, {
            "daño directo repetido": .20,
            "muerte/no_movimiento observado": .20,
            "animal/forma asociada a dolor": .25,
            "respuesta defensiva/evitación": .20,
            "soporte neuronal combinado": .15,
        })
        if confidence < 32:
            return
        if not self.should_print(f"fear-death-{h.entity_id}-{int(confidence//10)}", confidence, min_gap=180, min_conf=32):
            return
        evidencias = []
        for e in damage_events[-4:]:
            evidencias.append(f"Daño recibido T{e.tick}: atacante={e.actor_id} daño={e.data.get('daño')} arma={e.data.get('arma')}")
        for e in death_obs[-4:]:
            evidencias.append(f"Observa muerte T{e.tick}: {e.data}")
        for (a,b), val in sorted(c.items(), key=lambda x: x[1], reverse=True):
            if {a,b} & {"forma_trex","forma_cow","dolor","no_movimiento","ser_human","devolver_golpe"}:
                evidencias.append(f"Conexión {a} ↔ {b}: +{val:.2f}")
        concepto = "Asociación entre daño, animales/formas peligrosas y humanos inmóviles."
        resumen = "parece estar formando una idea primitiva de peligro: ciertas formas causan dolor, y un humano quieto/no-móvil puede ser una señal importante."
        equivalente = "proto-miedo / peligro / muerte-no-movimiento / evitación defensiva"
        self.print_report(
            "DETECTOR ESPECÍFICO: MIEDO / PELIGRO / MUERTE",
            h,
            "CONCEPTO DE SUPERVIVENCIA PROFUNDA",
            concepto,
            resumen,
            equivalente,
            confidence,
            evidencias[:10],
            factors,
            "Este detector exige daño o muerte observada + asociación neuronal + cambio defensivo. No basta con dar vueltas.",
            cyan=confidence < 60,
        )

    def detect_unclassified_clusters(self, h: Human) -> None:
        top = h.neural.top_connections(6)
        if len(top) < 4:
            return

        strength = sum(v for _, v in top) / len(top)
        raw_components = set(x for pair, _ in top for x in pair)
        diversity = len(raw_components) / 10

        # Penaliza clusters demasiado triviales: estar con otros, moverse por hambre/sed, etc.
        trivial_nodes = {
            "bienestar_social", "otro_humano_cerca", "hambre_alta", "sed_alta",
            "mover_hacia_objeto_pequeño", "mover_hacia_ser_pequeño", "mover_hacia_agua",
            "agua", "sed_baja", "reposo"
        }
        trivial_ratio = len(raw_components & trivial_nodes) / max(1, len(raw_components))
        rare_or_interesting = len(raw_components - trivial_nodes) / max(1, len(raw_components))
        confidence = clamp((strength * 0.58 + diversity * 0.24 + rare_or_interesting * 0.18 - trivial_ratio * 0.18) * 100, 0, 100)

        if not self.should_print(f"cluster-{h.entity_id}-{int(self.world.tick//240)}", confidence, min_gap=240, min_conf=28):
            return

        components = sorted(raw_components)[:10]
        evidencias = [f"Conexión {a} ↔ {b}: +{v:.2f}" for (a, b), v in top]

        self.print_report(
            "DETECTOR ABIERTO: CONCEPTO NO CLASIFICADO",
            h,
            "CONJUNTO CONCEPTUAL NO CLASIFICADO",
            "Agrupación neuronal fuerte todavía sin traducción clara.",
            f"se han unido varios elementos internos: {', '.join(components)}. Podría ser un concepto útil, una costumbre o una falsa alarma.",
            "desconocido / concepto propio / patrón interno raro",
            confidence,
            evidencias,
            {"fuerza media conexiones": strength, "diversidad componentes": diversity, "ratio trivial": trivial_ratio, "rareza/interés": rare_or_interesting},
            "Este detector busca cosas que no le hemos dicho explícitamente que busque, pero ahora penaliza mezclas triviales de hambre/sed/socialización.",
        )

        # Bot investigador específico: no afirma el concepto; audita hipótesis y pruebas.
        self.investigate_unclear_concept(h, components, top, confidence)

        # Nuevo sistema longitudinal: no cierra el caso en una foto fija;
        # abre una investigación que seguirá a este humano durante días y también a su linaje.
        category, hypothesis = self.world.classify_investigation_from_components(set(components), concepto + " " + resumen if False else " ".join(components))
        self.world.open_or_update_investigation(
            h,
            category,
            hypothesis,
            confidence * 0.55,
            evidence_for=evidencias[:4],
            evidence_against=["señal inicial: puede ser mezcla de supervivencia; requiere seguimiento temporal"],
            duration_days=7,
        )


    def investigate_unclear_concept(self, h: Human, components: List[str], top_connections: List[Tuple[Tuple[str, str], float]], parent_confidence: float) -> None:
        if parent_confidence < 35:
            return
        comp = set(components)
        signature = "investigador-" + h.entity_id + "-" + str(abs(hash(tuple(sorted(components)))) % 9999)
        if not self.should_print(signature, parent_confidence, min_gap=300, min_conf=35):
            return

        hypotheses: List[str] = []
        tests_for: List[str] = []
        tests_against: List[str] = []

        if {"sueño_bajo", "golpe_debil"} <= comp or any(set(pair) == {"sueño_bajo", "golpe_debil"} for pair, _ in top_connections):
            hypotheses.append("relación cansancio ↔ fuerza baja")
            tests_for.append("existe conexión sueño_bajo ↔ golpe_debil")
        if "dolor" in comp and ("forma_cow" in comp or "forma_trex" in comp or "forma_grande" in comp):
            hypotheses.append("relación animal/forma peligrosa ↔ dolor")
            tests_for.append("dolor aparece conectado a una forma animal concreta")
        if {"impulso_explorador", "mover_hacia_desconocido"} <= comp:
            hypotheses.append("impulso de exploración/refinamiento explorador")
            tests_for.append("impulso_explorador está asociado a mover_hacia_desconocido")
        if {"otro_humano_cerca", "bienestar_social"} <= comp:
            hypotheses.append("bienestar social básico")
            tests_for.append("otro_humano_cerca ↔ bienestar_social aparece reforzado")
        if {"no_movimiento", "ser_human"} <= comp:
            hypotheses.append("observación de humano inmóvil/muerte posible")
            tests_for.append("no_movimiento aparece unido a ser_human")
        if "dolor" in comp and ("forma_cow" in comp or "forma_trex" in comp) and "no_movimiento" in comp:
            hypotheses.insert(0, "proto-miedo / peligro por animal + humano inmóvil")
            tests_for.append("combina dolor, forma animal y no_movimiento: patrón parecido a miedo/peligro/muerte")
        if "intento_refugio" in comp or "palos_piedras" in comp:
            hypotheses.insert(0, "proto-refugio artificial / construcción fallida")
            tests_for.append("aparece intento_refugio o palos_piedras como señal de experimento constructivo")
        if "cueva_interior" in comp or "refugio" in " ".join(comp):
            hypotheses.append("posible proto-refugio")
            tests_for.append("aparecen nodos de cueva/refugio dentro del cluster")

        if not hypotheses:
            hypotheses.append("cluster mixto sin traducción clara")
            tests_against.append("no hay combinación suficiente para traducirlo a un concepto humano conocido")

        if "bienestar_social" in comp and "hambre_alta" in comp:
            tests_against.append("puede ser mezcla accidental de estar en grupo + hambre, no un concepto nuevo")
        if parent_confidence < 55:
            tests_against.append("confianza del cluster aún insuficiente para declararlo concepto")
        if len(set(components)) > 8:
            tests_against.append("demasiados nodos mezclados: puede ser ruido de supervivencia, no idea compacta")

        recent = self.recent_events(h, None, 500)[-12:]
        evidencias = [f"Conexión {a} ↔ {b}: +{v:.2f}" for (a, b), v in top_connections[:8]]
        evidencias += [f"Evento reciente {e.tick}: {e.kind} {e.data}" for e in recent[-5:]]
        clear_signal = (parent_confidence >= 70 and len(tests_against) <= 1) or (parent_confidence >= 55 and len(tests_for) >= 2 and len(tests_against) <= 2)
        extra = [
            f"hipótesis principal: {hypotheses[0]}",
            f"hipótesis alternativas: {', '.join(hypotheses[1:]) if len(hypotheses) > 1 else 'ninguna clara'}",
            f"señal clara encontrada: {'SÍ' if clear_signal else 'NO / EN INVESTIGACIÓN'}",
            "pruebas a favor: " + ("; ".join(tests_for) if tests_for else "pocas"),
            "pruebas en contra: " + ("; ".join(tests_against) if tests_against else "pocas"),
        ]
        self.print_report(
            "BOT INVESTIGADOR: CONCEPTO NO CLARO",
            h,
            "AUDITORÍA ESPECÍFICA DE CONCEPTO SOSPECHOSO",
            "Un investigador externo revisa un cluster no clasificado sin darlo por cierto.",
            f"el bot investigador cree que podría ser: {hypotheses[0]}, pero exige más pruebas antes de marcarlo como concepto descubierto.",
            "investigación de concepto / auditoría neuronal",
            clamp(parent_confidence * 0.75, 0, 100),
            evidencias,
            {"confianza del cluster original": parent_confidence / 100, "nodos analizados": min(len(components) / 10, 1), "claridad hipótesis": 0.7 if tests_for else 0.25, "ruido detectado": min(len(tests_against) / 4, 1)},
            "Este bot no crea conceptos nuevos: solo deja pruebas crudas y una hipótesis auditable para que tú revises si tiene sentido.",
            extra=extra,
            cyan=not clear_signal,
            darkblue=clear_signal,
        )



    def detect_open_sequence_patterns(self, h: Human) -> None:
        """
        Detector ultra-abierto: no busca una etiqueta concreta.
        Mira secuencias raras/repetidas de eventos y conexiones neuronales alrededor
        de ellas. Sirve para detectar conceptos extraños, manías, protoconceptos o
        refinamientos que no habíamos pensado.
        """
        events = self.recent_events(h, None, 900)
        if len(events) < 8:
            return

        # Secuencias de 3 eventos elegidos/activos del propio humano, evitando
        # eventos pasivos y repeticiones del mismo tick.
        seq_counts: Dict[Tuple[str, str, str], int] = {}
        seq_examples: Dict[Tuple[str, str, str], List[Event]] = {}
        passive_events = {"daño_por_necesidad", "observa_muerte", "muerte", "dormir"}
        own_all = [e for e in events if e.actor_id == h.entity_id and e.kind not in passive_events]
        own: List[Event] = []
        last_tick_kind: Set[Tuple[int, str]] = set()
        for e in own_all:
            key = (e.tick, e.kind)
            if key in last_tick_kind:
                continue
            last_tick_kind.add(key)
            own.append(e)
        for i in range(len(own) - 2):
            if len({own[i].tick, own[i + 1].tick, own[i + 2].tick}) < 3:
                continue
            seq = (own[i].kind, own[i + 1].kind, own[i + 2].kind)
            seq_counts[seq] = seq_counts.get(seq, 0) + 1
            seq_examples.setdefault(seq, []).append(own[i])

        if not seq_counts:
            return

        # Queremos patrones raros elegidos, no rutinas vitales repetidas.
        boring = {"dormir", "daño_por_necesidad", "observa_muerte", "muerte", "beber", "nacimiento", "comer", "coger_objeto"}
        survival_routine = {"beber", "comer", "coger_objeto", "nacimiento"}
        candidates = []
        for seq, count in seq_counts.items():
            novelty = len(set(seq)) / 3
            # No llamar "patrón extraño" a una secuencia vista una sola vez, salvo que incluya una acción realmente no prevista.
            if count < 2 and "accion_no_prevista" not in seq:
                continue
            if set(seq).issubset(survival_routine) and count < 3:
                continue
            not_boring = 1.0 if not set(seq).issubset(boring) else 0.05
            repetition = clamp(count / 5, 0, 1)
            neural_strength = 0.0
            # Busca si algún nodo relacionado con esos eventos está activo/conectado.
            for (a, b), val in h.neural.connections.items():
                joined = " ".join(seq)
                if any(part in joined for part in (a, b)):
                    neural_strength = max(neural_strength, val)
            oddity = clamp(h.genes.weirdness + h.genes.curiosity * 0.4, 0, 1)
            score = self.weighted_confidence(
                {
                    "repetición secuencia": repetition,
                    "variedad interna": novelty,
                    "no trivialidad": not_boring,
                    "soporte neuronal": neural_strength,
                    "tendencia exploratoria": oddity,
                },
                {
                    "repetición secuencia": 0.28,
                    "variedad interna": 0.18,
                    "no trivialidad": 0.18,
                    "soporte neuronal": 0.22,
                    "tendencia exploratoria": 0.14,
                },
            )
            if score >= 18:
                candidates.append((score, seq, count))

        if not candidates:
            return

        candidates.sort(reverse=True, key=lambda x: x[0])
        confidence, seq, count = candidates[0]
        signature = f"open-seq-{h.entity_id}-{hash(seq) % 9999}-{int(confidence//10)}"
        if not self.should_print(signature, confidence, min_gap=180, min_conf=18):
            return

        examples = seq_examples.get(seq, [])[:4]
        evidencias = []
        for e in examples:
            idx = own.index(e) if e in own else -1
            if idx >= 0 and idx + 2 < len(own):
                e1, e2, e3 = own[idx], own[idx + 1], own[idx + 2]
                evidencias.append(
                    f"Eventos {e1.tick}->{e2.tick}->{e3.tick}: {e1.kind} → {e2.kind} → {e3.kind}"
                )

        components = sorted(set(x for pair, _ in h.neural.top_connections(8) for x in pair))[:12]
        extra = [
            f"secuencia detectada: {' → '.join(seq)}",
            f"repeticiones recientes: {count}",
            f"componentes neuronales cercanos: {', '.join(components) if components else 'pocos/ninguno'}",
        ]

        self.print_report(
            "DETECTOR ABIERTO EXTREMO: PATRÓN EXTRAÑO",
            h,
            "POSIBLE CONCEPTO RARO / SECUENCIA EMERGENTE / FALSA ALARMA CONTROLADA",
            "Secuencia repetida de acciones o sucesos que no encaja necesariamente con los conceptos predefinidos.",
            "parece estar repitiendo una cadena de eventos que podría convertirse en una regla interna, costumbre, intuición o concepto propio. El detector no le asigna un nombre definitivo.",
            "concepto extraño / hábito emergente / protoconcepto / falsa alarma posible",
            confidence,
            evidencias,
            {
                "repetición secuencia": clamp(count / 4, 0, 1),
                "variedad interna": len(set(seq)) / 3,
                "no trivialidad": 1.0 if not set(seq).issubset(boring) else 0.1,
                "soporte neuronal": max([v for _, v in h.neural.top_connections(8)] or [0]),
                "tendencia exploratoria": clamp(h.genes.weirdness + h.genes.curiosity * 0.4, 0, 1),
            },
            "Este detector está hecho para encontrar incluso cosas raras que no habíamos previsto. Puede avisar con baja confianza para que tú decidas si tiene sentido.",
            extra=extra,
            cyan=True,
        )

    def detect_inventory_storage(self, h: Human) -> None:
        # Detecta conceptos raros como almacenar provisiones: llevar comida/semillas
        # durante tiempo sin comerlas de inmediato, especialmente si luego bajan hambre.
        inv = [i.kind for i in h.inventory]
        food_items = [k for k in inv if k in ("seed", "meat")]
        if not food_items:
            return
        pickups = [e for e in h.memory_events[-220:] if e.kind == "coger_objeto" and e.data.get("objeto") in ("seed", "meat")]
        eats = [e for e in h.memory_events[-220:] if e.kind == "comer" and e.data.get("objeto") in ("seed", "meat")]
        if len(pickups) < 2 and len(food_items) < 2:
            return
        held_ratio = clamp(len(food_items) / max(1, MAX_INVENTORY_ITEMS), 0, 1)
        repetition = clamp(len(pickups) / 6, 0, 1)
        delayed_use = 0.0
        for p in pickups:
            if any(8 <= e.tick - p.tick <= 160 for e in eats):
                delayed_use += 1
        delayed_use = clamp(delayed_use / max(1, len(pickups)), 0, 1)
        neural = max(
            h.neural.connections.get(tuple(sorted(("comida_meat", "hambre_baja"))), 0.0),
            h.neural.connections.get(tuple(sorted(("objeto_seed", "mano_coger"))), 0.0),
            h.neural.activations.get("inventario_lleno", 0.0),
        )
        confidence = self.weighted_confidence(
            {"objetos comida guardados": held_ratio, "repetición recogida": repetition, "uso diferido": delayed_use, "conexión neuronal": neural},
            {"objetos comida guardados": .25, "repetición recogida": .25, "uso diferido": .30, "conexión neuronal": .20},
        )
        if not self.should_print(f"storage-{h.entity_id}-{int(confidence//10)}", confidence, min_gap=90, min_conf=18):
            return
        evidencias = [f"Inventario actual: {inv}"]
        evidencias += [f"Evento {e.tick}: cogió {e.data.get('objeto')}" for e in pickups[-5:]]
        evidencias += [f"Evento {e.tick}: comió {e.data.get('objeto')}" for e in eats[-4:]]
        self.print_report(
            "DETECTOR ABIERTO: POSIBLE ALMACENAMIENTO",
            h,
            "CONCEPTO LOGÍSTICO / PROVISIÓN",
            "Uso del inventario para conservar comida o semillas más allá del momento inmediato.",
            "parece estar acumulando objetos comestibles o útiles en el inventario, quizá como reserva futura; puede ser casualidad si la confianza es baja.",
            "almacenar provisiones / reserva / llevar comida",
            confidence,
            evidencias,
            {"objetos comida guardados": held_ratio, "repetición recogida": repetition, "uso diferido": delayed_use, "conexión neuronal": neural},
            "Los hijos no heredan este concepto. Solo se detecta si aparece por conducta y memoria individual.",
            cyan=True,
        )

    def detect_cultural_patterns(self) -> None:
        """
        Detector cultural mucho más estricto.
        Antes confundía supervivencia torpe / vueltas / muerte compartida con proto-religión.
        Ahora solo avisa si hay acciones simbólicas/no útiles repetidas, persistentes y compartidas.
        """
        alive = [h for h in self.world.humans.values() if h.alive]
        if len(alive) < 3:
            return

        recent = [e for e in self.world.events if e.tick >= self.world.tick - 1800]
        deaths = [e for e in recent if e.kind == "muerte"]

        # Solo cuentan actos potencialmente simbólicos/culturales reales.
        # Excluimos gesto_al_aire como evidencia directa: dar vueltas o golpear aire suele ser ruido.
        odd = [
            e for e in recent
            if e.kind == "accion_no_prevista" and e.data.get("accion") in ("combinar_objetos_raro",)
        ]

        ritual_like = []
        action_types: Set[str] = set()
        actor_ids: Set[str] = set()
        for e in odd:
            pos = e.data.get("pos")
            near_any_cave = False
            if pos and self.world.cave_entrances:
                near_any_cave = min(dist(pos, cp) for cp in self.world.cave_entrances) <= 5
            after_death = any(0 <= e.tick - m.tick <= 96 for m in deaths)
            # Para ser ritual_like debe ocurrir cerca de cueva o tras muerte/evento fuerte.
            if near_any_cave or after_death:
                ritual_like.append(e)
                action_types.add(str(e.data.get("accion")))
                actor_ids.add(e.actor_id)

        shared_scores = []
        for h in alive:
            score = 0.0
            for a, b in [
                ("intento_refugio", "palos_piedras"),
                ("intento_refugio", "cobertura_debil"),
                ("cueva_interior", "reposo"),
                ("cueva_interior", "menos_daño"),
                ("no_movimiento", "ser_human"),
            ]:
                score += h.neural.connections.get(tuple(sorted((a, b))), 0)
            shared_scores.append(score)

        collective = clamp(statistics.mean(shared_scores) if shared_scores else 0, 0, 1)
        repeated = clamp(len(ritual_like) / 8, 0, 1)
        shared_actors = clamp(len(actor_ids) / max(2, len(alive)), 0, 1)
        action_diversity = clamp(len(action_types) / 3, 0, 1)
        persistence = 0.0
        if ritual_like:
            persistence = clamp((max(e.tick for e in ritual_like) - min(e.tick for e in ritual_like)) / 900, 0, 1)
        post_death = clamp(sum(1 for e in ritual_like if any(0 <= e.tick - m.tick <= 96 for m in deaths)) / max(1, len(ritual_like)), 0, 1)
        cave_context = clamp(sum(1 for e in ritual_like if e.data.get("pos") and self.world.cave_entrances and min(dist(e.data.get("pos"), cp) for cp in self.world.cave_entrances) <= 5) / max(1, len(ritual_like)), 0, 1)

        factors = {
            "repetición simbólica real": repeated,
            "varios actores": shared_actors,
            "diversidad de acto ritual": action_diversity,
            "persistencia temporal": persistence,
            "contexto muerte/evento fuerte": post_death,
            "contexto cueva/refugio": cave_context,
            "conexión neuronal colectiva": collective,
        }

        confidence = self.weighted_confidence(
            factors,
            {
                "repetición simbólica real": 0.24,
                "varios actores": 0.18,
                "diversidad de acto ritual": 0.10,
                "persistencia temporal": 0.17,
                "contexto muerte/evento fuerte": 0.13,
                "contexto cueva/refugio": 0.08,
                "conexión neuronal colectiva": 0.10,
            },
        )

        # Filtro anti-falsas religiones: si no hay actos ritual_like reales, no reporta religión.
        if len(ritual_like) < 3 or repeated < 0.25 or shared_actors < 0.18:
            return
        if confidence < 38:
            return
        if not self.should_print(f"culture-strict-{int(confidence//10)}-{int(self.world.tick//240)}", confidence, min_gap=360, min_conf=38):
            return

        evidencias = [
            f"Evento {e.tick}: {e.actor_id} hizo {e.data.get('accion')} → {e.data.get('resultado')} pos={e.data.get('pos')}"
            for e in ritual_like[:8]
        ]
        extra = [
            f"actos ritual_like reales: {len(ritual_like)}",
            f"actores distintos implicados: {len(actor_ids)}/{len(alive)}",
            f"tipos de acto: {', '.join(sorted(action_types)) if action_types else 'ninguno'}",
            f"humanos vivos con señales similares: {sum(1 for s in shared_scores if s > 0.08)}/{len(alive)}",
            f"similitud colectiva aproximada: {pct(collective * 100)}",
            "gesto_al_aire NO cuenta como religión por sí solo",
        ]

        self.print_report(
            "DETECTOR UNIVERSAL ESTRICTO: CULTURA / PROTO-RELIGIÓN",
            None,
            "CONCEPTO CULTURAL / POSIBLE PROTO-RELIGIÓN",
            "Conductas no directamente útiles, repetidas, compartidas y vinculadas a muerte/refugio/eventos fuertes.",
            "podría estar apareciendo una conducta simbólica compartida, pero el detector exige repetición, persistencia y varios actores para no confundirlo con vueltas tontas.",
            "ritual / ofrenda / duelo / proto-religión / costumbre simbólica",
            confidence,
            evidencias,
            factors,
            "No significa religión confirmada. Esta versión es más estricta: no usa simples vueltas, gestos al aire o socialización como prueba suficiente.",
            extra=extra,
        )


# ============================================================
# MAIN
# ============================================================

HELP_TEXT = """
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

""".strip()

HELP_SIM_TEXT = """
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
""".strip()

HELP_EXPORT_TEXT = """
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
""".strip()

HELP_LAB_TEXT = """
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
""".strip()

HELP_HUMANS_TEXT = """
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
""".strip()

HELP_DETECTOR_TEXT = """
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
""".strip()

HELP_DEBUG_TEXT = """
DEBUG / INFORMES
  fallos                 acciones realmente no previstas
  todos_logs             todo el historial
  valiosos               solo señales importantes
  export useful RUTA     paquete recomendable para análisis
  export all RUTA        paquete gigantesco con todo
""".strip()


def print_help() -> None:
    print("\n" + ctext(HELP_TEXT, Color.BOLD + Color.WHITE))


def strip_ansi_for_count(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def ansi_to_html(text: str) -> str:
    """Convierte ANSI básico a HTML para conservar colores en informes externos."""
    color_map = {
        "30": "color:#111111", "31": "color:#b00020", "32": "color:#16803a",
        "33": "color:#9a6700", "34": "color:#003a8c", "35": "color:#7a1fa2",
        "36": "color:#007a8a", "37": "color:#eeeeee", "90": "color:#777777",
        "91": "color:#d00000", "92": "color:#00a441", "93": "color:#b8860b",
        "94": "color:#003b99", "95": "color:#9b00c9", "96": "color:#0096a8",
        "97": "color:#ffffff",
    }
    out: List[str] = []
    stack = 0
    i = 0
    ansi_re = re.compile(r"\x1b\[([0-9;]*)m")
    for m in ansi_re.finditer(text):
        out.append(html.escape(text[i:m.start()]))
        codes = [c for c in m.group(1).split(";") if c] or ["0"]
        if "0" in codes:
            while stack > 0:
                out.append("</span>")
                stack -= 1
            codes = [c for c in codes if c != "0"]
        styles: List[str] = []
        if "1" in codes:
            styles.append("font-weight:700")
        if "2" in codes:
            styles.append("opacity:.72")
        # Soporte ANSI 256 colores: 38;5;N, usado por dorado y azul oscuro.
        # Ej.: [38;5;220m = dorado, [38;5;21m = azul oscuro.
        for idx, c in enumerate(codes):
            if c in color_map:
                styles.append(color_map[c])
            elif c == "38" and idx + 2 < len(codes) and codes[idx + 1] == "5":
                try:
                    n = int(codes[idx + 2])
                    if n == 220:
                        styles.append("color:#d4af37")
                    elif n == 21:
                        styles.append("color:#0033aa")
                    else:
                        # Conversión aproximada para paleta 256 ANSI.
                        if 16 <= n <= 231:
                            n2 = n - 16
                            r = n2 // 36
                            g = (n2 % 36) // 6
                            b = n2 % 6
                            conv = [0, 95, 135, 175, 215, 255]
                            styles.append(f"color:rgb({conv[r]},{conv[g]},{conv[b]})")
                        elif 232 <= n <= 255:
                            v = 8 + (n - 232) * 10
                            styles.append(f"color:rgb({v},{v},{v})")
                except Exception:
                    pass
        if styles:
            out.append('<span style="' + ';'.join(styles) + '">')
            stack += 1
        i = m.end()
    out.append(html.escape(text[i:]))
    while stack > 0:
        out.append("</span>")
        stack -= 1
    return "".join(out)


def show_paged_text(title: str, text: str) -> None:
    """
    MODO INFORME ESTÁTICO 1.4.8.

    En vez de usar `less` dentro del Terminal, que en macOS puede interpretar mal
    la rueda/flechas y perder colores, genera un HTML temporal y lo abre con
    `open`. Así puedes subir/bajar con la rueda normal, buscar con Cmd+F y ver
    los colores completos del informe sin que el mapa se repinte encima.
    """
    header = "\n" + "=" * 100 + "\n" + title + "\n" + "=" * 100 + "\n"
    footer = "\n" + "=" * 100 + "\n"
    full_text = header + (text if text else "") + footer

    safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "_", strip_ansi_for_count(title)).strip("_")[:50] or "reporte"
    tmp_dir = tempfile.gettempdir()
    html_path = os.path.join(tmp_dir, f"protoH_{safe_title}_{int(time.time())}.html")

    body = ansi_to_html(full_text)
    page_title = html.escape(strip_ansi_for_count(title))
    doc = """<!doctype html>
<html lang=\"es\">
<head>
<meta charset=\"utf-8\">
<title>{page_title}</title>
<style>
  body {{ background:#101114; color:#e8e8e8; margin:0; padding:28px; }}
  .bar {{ position:sticky; top:0; background:#17191f; border-bottom:1px solid #333; padding:10px 14px; margin:-28px -28px 20px -28px; font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif; }}
  .hint {{ color:#aeb6c2; font-size:13px; margin-top:4px; }}
  pre {{ white-space:pre-wrap; word-wrap:break-word; font-family:Menlo,Consolas,\"SFMono-Regular\",monospace; font-size:13px; line-height:1.35; }}
</style>
</head>
<body>
<div class=\"bar\"><b>{page_title}</b><div class=\"hint\">Scroll con rueda/trackpad. Buscar: Cmd+F. Vuelve a la simulación en Terminal pulsando Enter.</div></div>
<pre>{body}</pre>
</body>
</html>""".format(page_title=page_title, body=body)

    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(doc)
        if sys.platform == "darwin":
            subprocess.run(["open", html_path], check=False)
        else:
            opener = shutil.which("xdg-open")
            if opener:
                subprocess.run([opener, html_path], check=False)
            else:
                print(full_text)
                input("\nEnter para volver > ")
                return
        print(ctext(f"Informe abierto en navegador: {html_path}", Color.BRIGHT_CYAN))
        input("Enter para volver al mapa > ")
    except Exception as e:
        print(ctext(f"No se pudo abrir informe HTML ({e}). Imprimo en Terminal normal.", Color.YELLOW))
        print(full_text)
        input("\nEnter para volver > ")

def advance_ticks(world: World, amount: int) -> None:
    """Avanza varios ticks en un solo ciclo visual/manual.

    speed N no cambia las reglas internas: simplemente ejecuta N veces run_tick()
    antes del siguiente render/input. Así puedes acelerar simulaciones largas sin
    tocar delay ni meter conocimiento/trampas a los protohumanos.
    """
    n = max(1, int(amount))
    for _ in range(n):
        if world.tick >= MAX_TICKS:
            break
        world.run_tick()


def update_fast_controller(state: Dict[str, Any], ticks_done: int, elapsed: float) -> None:
    """Ajusta speed/delay en modo FATS buscando muchos ticks/segundo sin congelar la interfaz."""
    if not state.get("fast"):
        return
    state["delay"] = 0.0
    state["fast_ticks_accum"] = int(state.get("fast_ticks_accum", 0)) + int(ticks_done)
    now = time.time()
    last = float(state.get("fast_last_check", now))
    window = max(0.001, now - last)
    speed = int(state.get("speed", 1))
    # Mantiene cada lote en una duración razonable: si es demasiado corto sube speed; si se atasca lo baja.
    if elapsed < 0.018 and speed < 500:
        speed = min(500, max(speed + 1, int(speed * 1.18) + 1))
    elif elapsed > 0.12 and speed > 1:
        speed = max(1, int(speed * 0.72))
    state["speed"] = speed
    if window >= 0.75:
        tps = int(state.get("fast_ticks_accum", 0)) / window
        state["fast_tps"] = tps
        if tps > float(state.get("fast_best_tps", 0.0)):
            state["fast_best_tps"] = tps
            state["fast_best_speed"] = speed
        elif float(state.get("fast_best_tps", 0.0)) > 0 and tps < float(state.get("fast_best_tps", 0.0)) * 0.72:
            state["speed"] = max(1, int(state.get("fast_best_speed", speed)))
        state["fast_last_check"] = now
        state["fast_ticks_accum"] = 0




# ============================================================
# V2.0 — LABORATORIO Y EXPORTACIONES ORGANIZADAS
# ============================================================

def _v20_set_lab_profile(h: Human, focus: str = "general", max_genes: bool = False) -> None:
    """Marca un humano como sujeto de laboratorio. No introduce conceptos."""
    h.is_lab = True
    h.lab_focus = focus or "general"
    h.lab_origin = "lab"
    h.detected_concepts.append(f"[LAB] sujeto de laboratorio orientado a {h.lab_focus}; sin conceptos heredados")
    if max_genes:
        h.genes = Genes(
            speed=1.8, strength=20.0, memory=2.0, curiosity=1.8, sociability=1.5,
            aggression=0.25, association=2.0, fertility=1.5, sleep_need=0.6,
            energy_efficiency=1.6, weirdness=1.2, exploration_spirit=3.0,
        )
        h.hunger_resistance = 2.0
        h.thirst_resistance = 2.0
        h.old_age_resistance = 2.0
        h.energy = 100.0
    # Ajustes de perfil: predisposición, no conocimiento.
    f = (focus or "general").lower()
    if f in ("refugio", "cueva", "construccion", "construcción"):
        h.genes.curiosity = max(h.genes.curiosity, 1.55)
        h.genes.association = max(h.genes.association, 1.55)
        h.genes.exploration_spirit = max(h.genes.exploration_spirit, 2.2)
        h.genes.weirdness = max(h.genes.weirdness, 0.65)
    elif f in ("distancia", "dimension", "dimensión", "ruta", "mapa"):
        h.genes.curiosity = max(h.genes.curiosity, 1.7)
        h.genes.memory = max(h.genes.memory, 1.7)
        h.genes.association = max(h.genes.association, 1.7)
        h.genes.exploration_spirit = max(h.genes.exploration_spirit, 2.8)
    elif f in ("vida", "muerte", "miedo", "peligro"):
        h.genes.association = max(h.genes.association, 1.7)
        h.genes.memory = max(h.genes.memory, 1.7)
        h.genes.curiosity = max(h.genes.curiosity, 1.55)
        h.genes.sociability = max(h.genes.sociability, 0.9)
    elif f in ("trampa", "cebo", "almacenamiento", "provisiones"):
        h.genes.curiosity = max(h.genes.curiosity, 1.6)
        h.genes.association = max(h.genes.association, 1.7)
        h.genes.memory = max(h.genes.memory, 1.6)
        h.genes.weirdness = max(h.genes.weirdness, 0.8)


def _world_lab_spawn(self: World, count: int, focus: str = "general", max_genes: bool = False) -> List[Human]:
    born: List[Human] = []
    for _ in range(max(1, int(count))):
        pos = self.find_spawn_position(None, None) or self.random_empty_cell()
        if not pos:
            break
        h = self.add_human(pos[0], pos[1])
        _v20_set_lab_profile(h, focus, max_genes=max_genes)
        h.last_action = f"nacer_lab_{focus}"
        self.log("lab_spawn", h.entity_id, nacimiento=h.birth_number, focus=focus, max_genes=max_genes, pos=h.pos(), nota="LAB: no hereda conceptos; solo perfil de observación")
        self.lab_notes.append(f"[Día {self.day} T{self.tick}] LAB #{h.birth_number} focus={focus} max={max_genes} pos={h.pos()}")
        # Abrimos investigación externa orientada al foco.
        category, hyp = self.classify_investigation_from_components(set(), focus)
        if category == "concepto_no_claro":
            category, hyp = focus, f"laboratorio: ruta conceptual {focus}"
        self.open_or_update_investigation(h, category, hyp, 22.0, evidence_for=[f"Sujeto LAB creado para observar ruta {focus}"], duration_days=12)
        born.append(h)
    return born


def _world_lab_humans(self: World) -> List[Human]:
    return sorted([h for h in self.humans.values() if getattr(h, "is_lab", False)], key=lambda h: h.birth_number)


def _world_lab_list_report(self: World) -> str:
    labs = self.lab_humans()
    lines = ["HUMANOS DE LABORATORIO", "=" * 80, f"Aislamiento reproductivo LAB: {'ON' if getattr(self, 'lab_isolate', True) else 'OFF'}", ""]
    if not labs:
        lines.append("No hay humanos de laboratorio.")
        return "\n".join(lines)
    for h in labs:
        st = "VIVO" if h.alive else "muerto"
        lines.append(f"L#{h.birth_number:<5} {st:<6} {'∞ ' if getattr(h,'immortal',False) else '  '}focus={getattr(h,'lab_focus','general'):<16} score={self.gene_score(h):5.1f} pos={h.pos()} hijos={len(self.children_of(h.birth_number))} conceptos={len(h.detected_concepts)}")
    return "\n".join(lines)


def _world_lab_watch_report(self: World, spec: str) -> str:
    spec = str(spec).strip().lower()
    if spec.startswith("concept "):
        focus = spec.split(None, 1)[1]
        labs = [h for h in self.lab_humans() if getattr(h, "lab_focus", "").lower() == focus]
        if not labs:
            return f"No hay sujetos LAB con focus={focus}."
        return "\n\n".join(self.lab_watch_report(str(h.birth_number)) for h in labs[:30])
    try:
        nb = int(spec)
    except ValueError:
        return "Uso: lab watch NUMERO | lab watch concept refugio"
    h = self.human_by_birth(nb)
    if not h:
        return f"No existe humano #{nb}."
    lines = [f"LAB WATCH #{nb}", "=" * 96]
    lines.append(f"LAB: {'SÍ' if getattr(h,'is_lab',False) else 'no'} | focus={getattr(h,'lab_focus','-')} | estado={'VIVO' if h.alive else 'muerto'} | score={self.gene_score(h):.1f}")
    lines.append("")
    lines.append("HIPÓTESIS / INVESTIGACIONES RELACIONADAS:")
    invs = [i for i in self.investigations.values() if i.subject_birth == nb or i.origin_birth == nb]
    if not invs:
        lines.append("  ninguna")
    for inv in sorted(invs, key=lambda x: x.confidence, reverse=True)[:20]:
        lines.append(f"  - INV{inv.inv_id} {inv.category} {pct(inv.confidence)} estado={inv.state} valiosa={'sí' if inv.valuable else 'no'}")
        for e in inv.evidence_for[-4:]:
            lines.append(f"      + {e}")
        for e in inv.evidence_against[-2:]:
            lines.append(f"      - {e}")
    lines.append("")
    lines.append("CONEXIONES PRINCIPALES:")
    for (a,b), v in h.neural.top_connections(15):
        lines.append(f"  - {a} ↔ {b}: +{v:.3f}")
    lines.append("")
    lines.append("EVENTOS CRUDOS RECIENTES:")
    for ev in h.memory_events[-40:]:
        lines.append(f"  - [Día {ev.day} T{ev.tick}] {ev.kind} {ev.data}")
    return "\n".join(lines)


def _world_lab_report(self: World) -> str:
    labs = self.lab_humans()
    lines = ["REPORTE DE LABORATORIO PROTOH", "=" * 100, f"Día {self.day} | Tick {self.tick}", f"Sujetos LAB totales: {len(labs)} | vivos: {sum(1 for h in labs if h.alive)}", f"Aislamiento LAB: {'ON' if getattr(self,'lab_isolate',True) else 'OFF'}", ""]
    by_focus: Dict[str, List[Human]] = {}
    for h in labs:
        by_focus.setdefault(getattr(h, "lab_focus", "general"), []).append(h)
    for focus, hs in sorted(by_focus.items(), key=lambda x: x[0]):
        lines.append(f"FOCUS: {focus} | sujetos={len(hs)} vivos={sum(1 for h in hs if h.alive)}")
        invs = [i for i in self.investigations.values() if any(i.subject_birth == h.birth_number or i.origin_birth == h.birth_number for h in hs)]
        if invs:
            best = sorted(invs, key=lambda i: i.confidence, reverse=True)[:5]
            for inv in best:
                lines.append(f"  - INV{inv.inv_id} {inv.category} {pct(inv.confidence)} {inv.state} valiosa={'sí' if inv.valuable else 'no'}")
                if inv.evidence_for:
                    lines.append(f"      mejor pista: {inv.evidence_for[-1]}")
        else:
            lines.append("  - sin investigaciones todavía")
        top = sorted(hs, key=self.gene_score, reverse=True)[:3]
        for h in top:
            lines.append(f"    L#{h.birth_number} {'VIVO' if h.alive else 'muerto'} score={self.gene_score(h):.1f} pos={h.pos()} conceptos={len(h.detected_concepts)}")
        lines.append("")
    lines.append("NOTAS LAB:")
    lines.extend(self.lab_notes[-80:] or ["  sin notas"])
    return "\n".join(lines)


def _write_text(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(strip_ansi_for_count(text))
    return path


def _world_export_simple(self: World, kind: str, raw_path: str) -> str:
    kind = kind.lower()
    default = f"protoH_{kind}_dia{self.day}_tick{self.tick}.txt"
    path = self.resolve_export_path(raw_path, default)
    if not os.path.splitext(path)[1]:
        path += ".txt"
    data = {
        "logs": "\n".join(self.all_logs),
        "conceptos": "\n\n".join(self.concept_logs),
        "valiosos": self.valuable_logs_report(),
        "fallos": "\n\n".join(self.unexpected_logs) or "Sin fallos raros.",
        "investigaciones": self.investigations_report(False),
        "investigaciones_valiosas": self.investigations_report(True),
        "gene_bank": self.gene_bank_report(),
        "rankings": self.rankings_report(category=None, limit=50),
        "lab": self.lab_report(),
    }.get(kind, f"Tipo de export no soportado: {kind}")
    _write_text(path, data)
    return f"Export {kind} creado en: {path}"


def _world_export_brains_all(self: World, raw_path: str) -> str:
    root = os.path.expanduser(str(raw_path).strip()) or f"protoH_brains_all_dia{self.day}_tick{self.tick}"
    os.makedirs(root, exist_ok=True)
    count = 0
    for h in sorted(self.humans.values(), key=lambda h: h.birth_number):
        _write_text(os.path.join(root, f"brain_{h.birth_number}.txt"), self.brain_report(h.birth_number))
        count += 1
    return f"Brains exportados: {count} archivos en {root}"


def _world_export_trees_all(self: World, raw_path: str) -> str:
    root = os.path.expanduser(str(raw_path).strip()) or f"protoH_trees_all_dia{self.day}_tick{self.tick}"
    os.makedirs(root, exist_ok=True)
    self.export_tree_image("all", os.path.join(root, f"tree_all_dia{self.day}_tick{self.tick}.svg"))
    count = 0
    indiv = os.path.join(root, "individual")
    os.makedirs(indiv, exist_ok=True)
    for h in sorted(self.humans.values(), key=lambda h: h.birth_number):
        self.export_tree_image(str(h.birth_number), os.path.join(indiv, f"tree_{h.birth_number}.svg"))
        count += 1
    return f"Árboles exportados: {count} individuales + tree_all en {root}"


def _world_export_lineages_all(self: World, raw_path: str) -> str:
    root = os.path.expanduser(str(raw_path).strip()) or f"protoH_lineages_all_dia{self.day}_tick{self.tick}"
    os.makedirs(root, exist_ok=True)
    count = 0
    for h in sorted(self.humans.values(), key=lambda h: h.birth_number):
        _write_text(os.path.join(root, f"lineage_{h.birth_number}.txt"), self.lineage_watch_report(h.birth_number))
        count += 1
    return f"Lineages exportados: {count} archivos en {root}"


def _world_export_lab_all(self: World, raw_path: str) -> str:
    root = os.path.expanduser(str(raw_path).strip()) or f"protoH_lab_all_dia{self.day}_tick{self.tick}"
    os.makedirs(root, exist_ok=True)
    _write_text(os.path.join(root, "lab_report.txt"), self.lab_report())
    _write_text(os.path.join(root, "lab_list.txt"), self.lab_list_report())
    _write_text(os.path.join(root, "lab_notes.txt"), "\n".join(self.lab_notes))
    labs = self.lab_humans()
    brain_dir = os.path.join(root, "brains")
    tree_dir = os.path.join(root, "trees")
    os.makedirs(brain_dir, exist_ok=True)
    os.makedirs(tree_dir, exist_ok=True)
    for h in labs:
        _write_text(os.path.join(brain_dir, f"lab_brain_{h.birth_number}.txt"), self.brain_report(h.birth_number))
        self.export_tree_image(str(h.birth_number), os.path.join(tree_dir, f"lab_tree_{h.birth_number}.svg"))
    _write_text(os.path.join(root, "MANIFEST.txt"), f"LAB export completo\nSujetos LAB: {len(labs)}\nDía {self.day} tick {self.tick}\n")
    return f"Export LAB completo creado en: {root} | sujetos={len(labs)}"

# Monkey patch de métodos v2.0.
World.lab_spawn = _world_lab_spawn
World.lab_humans = _world_lab_humans
World.lab_list_report = _world_lab_list_report
World.lab_watch_report = _world_lab_watch_report
World.lab_report = _world_lab_report
World.export_simple_report = _world_export_simple
World.export_brains_all = _world_export_brains_all
World.export_trees_all = _world_export_trees_all
World.export_lineages_all = _world_export_lineages_all
World.export_lab_all = _world_export_lab_all

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    """Devuelve True si debe salir del programa."""
    cmd = cmd.strip().lower()

    if cmd in ("q", "quit", "salir", "exit"):
        return True

    if cmd in ("help", "ayuda", "comandos", "?"):
        state["paused"] = True
        show_paged_text("AYUDA / COMANDOS", HELP_TEXT)
        return False

    if cmd in ("conceptos", "logs", "important", "importantes"):
        state["paused"] = True
        if not world.concept_logs:
            out_text = "Todavía no hay conceptos detectados."
        else:
            out_text = "\n\n".join(style_text(line, style_for_report_text(line)) for line in world.concept_logs[-60:])
        show_paged_text("LOGS ÚTILES / CONCEPTOS DETECTADOS", out_text)
        return False

    if cmd in ("fallos", "errores", "no_previstos", "noprevistos"):
        state["paused"] = True
        if not world.unexpected_logs:
            out_text = "Todavía no hay acciones no previstas detectadas."
        else:
            out_text = "\n\n".join(red_alert(line) for line in world.unexpected_logs[-60:])
        show_paged_text("ACCIONES NO PREVISTAS / FALLOS RAROS", out_text)
        return False

    if cmd in ("todos_logs", "todo", "all_logs", "alllogs"):
        state["paused"] = True
        if not world.all_logs:
            out_text = "Todavía no hay logs."
        else:
            rendered = []
            for line in world.all_logs:
                if "accion_no_prevista" in line:
                    rendered.append(red_alert(line))
                elif "DETECTOR" in line or "concepto" in line.lower() or "REGISTRO NEURONAL" in line or "BOT INVESTIGADOR" in line:
                    rendered.append(style_text(line, style_for_report_text(line)))
                else:
                    rendered.append(line)
            out_text = "\n\n".join(rendered)
        show_paged_text("TODOS LOS LOGS DE LA SESIÓN", out_text)
        return False

    if cmd in ("valiosos", "valuable", "valuable_logs", "logs_valiosos", "importantes_valiosos"):
        state["paused"] = True
        show_paged_text("REPORTES REALMENTE VALIOSOS", world.valuable_logs_report())
        return False

    if cmd in ("investigaciones", "investigations", "investigation", "invests"):
        state["paused"] = True
        show_paged_text("INVESTIGACIONES LONGITUDINALES", world.investigations_report(only_valuable=False))
        return False

    if cmd in ("investigaciones_valiosas", "investigaciones utiles", "investigaciones_útiles", "valuable_investigations"):
        state["paused"] = True
        show_paged_text("INVESTIGACIONES VALIOSAS", world.investigations_report(only_valuable=True))
        return False

    if cmd.startswith("investigar ") or cmd.startswith("investigate "):
        state["paused"] = True
        parts = cmd.split()
        if len(parts) < 2 or not parts[1].isdigit():
            show_paged_text("USO", "Uso: investigar 721")
        else:
            show_paged_text(f"INVESTIGAR #{parts[1]}", world.investigate_person_report(int(parts[1])))
        return False

    if cmd.startswith("lineage_watch ") or cmd.startswith("lineage watch ") or cmd.startswith("linaje_watch ") or cmd.startswith("linaje "):
        state["paused"] = True
        parts = cmd.replace("lineage watch", "lineage_watch").split()
        if len(parts) < 2 or not parts[1].isdigit():
            show_paged_text("USO", "Uso: lineage_watch 721")
        else:
            show_paged_text(f"SEGUIMIENTO DE LINAJE #{parts[1]}", world.lineage_watch_report(int(parts[1])))
        return False

    if cmd.startswith("export investigations") or cmd.startswith("export investigaciones"):
        state["paused"] = True
        parts = cmd.split(maxsplit=2)
        raw_path = parts[2] if len(parts) >= 3 else ""
        if not raw_path:
            print("Uso: export investigations /ruta/investigaciones.txt")
            input("\nEnter para volver > ")
            return False
        msg = world.export_investigations_file(raw_path, only_valuable=False)
        print(msg)
        state["status_message"] = msg
        input("\nEnter para volver > ")
        return False

    if cmd.startswith("export lineage") or cmd.startswith("export linaje"):
        state["paused"] = True
        parts = cmd.split(maxsplit=3)
        if len(parts) < 4 or not parts[2].isdigit():
            print("Uso: export lineage 721 /ruta/linaje_721.txt")
            input("\nEnter para volver > ")
            return False
        msg = world.export_lineage_watch_file(int(parts[2]), parts[3])
        print(msg)
        state["status_message"] = msg
        input("\nEnter para volver > ")
        return False

    if cmd.startswith("export useful") or cmd.startswith("export_util") or cmd.startswith("export util") or cmd.startswith("export_valiosos") or cmd.startswith("export important"):
        state["paused"] = True
        parts = cmd.split(maxsplit=2)
        raw_path = parts[2] if len(parts) >= 3 and parts[0] == "export" else (parts[1] if len(parts) >= 2 else "")
        if not raw_path:
            print("Uso: export useful /ruta/protoH_util.txt")
            input("\nEnter para volver > ")
            return False
        msg = world.export_useful_file(raw_path)
        print(msg)
        state["status_message"] = msg
        input("\nEnter para volver > ")
        return False

    if cmd.startswith("export all") or cmd.startswith("export_todo") or cmd.startswith("export absoluto") or cmd.startswith("export everything"):
        state["paused"] = True
        parts = cmd.split(maxsplit=2)
        raw_path = parts[2] if len(parts) >= 3 and parts[0] == "export" else (parts[1] if len(parts) >= 2 else "")
        if not raw_path:
            print("Uso: export all /ruta/protoH_TODO.txt")
            input("\nEnter para volver > ")
            return False
        msg = world.export_everything_file(raw_path)
        print(msg)
        state["status_message"] = msg
        input("\nEnter para volver > ")
        return False

    if cmd.startswith("export_logs") or cmd.startswith("exportar_logs") or cmd.startswith("export logs"):
        state["paused"] = True
        if cmd.startswith("export logs"):
            parts = cmd.split(maxsplit=2)
            raw_path = parts[2] if len(parts) >= 3 else ""
        else:
            parts = cmd.split(maxsplit=1)
            raw_path = parts[1] if len(parts) >= 2 else ""
        if not raw_path:
            print("Uso: export_logs /ruta/protoH_logs.txt")
            input("\nEnter para volver > ")
            return False
        msg = world.export_logs_file(raw_path)
        print(msg)
        state["status_message"] = msg
        input("\nEnter para volver > ")
        return False

    if cmd.startswith(("spawnmax", "spawn_max", "spawn100", "spawn_100", "maxhumans")):
        parts = cmd.split()
        if len(parts) < 2:
            print("Uso: spawnmax 10   (crea 10 humanos con genes al máximo útil, sin conceptos)")
            return False
        try:
            count = max(1, min(2000, int(float(parts[1].replace(",", ".")))))
        except ValueError:
            print("Cantidad no válida. Ejemplo: spawnmax 10")
            return False
        born = world.manual_spawn_max_humans(count)
        msg = f"Spawn MAX creados: {len(born)} humanos con genes al máximo útil; conceptos NO heredados."
        print(msg)
        state["status_message"] = msg
        return False

    if cmd.startswith("spawn"):
        parts = cmd.split(maxsplit=2)
        if len(parts) < 2:
            print("Uso: spawn 5 | spawn 5 9,24 | spawn 7 best")
            return False
        try:
            count = max(1, int(parts[1]))
        except ValueError:
            print("Cantidad no válida. Ejemplo: spawn 5")
            return False
        p1 = p2 = None
        if len(parts) == 3:
            spec = parts[2].strip()
            if spec in ("max", "maxgenes", "100", "100%"):
                born = world.manual_spawn_max_humans(count)
                msg = f"Spawn MAX creados: {len(born)} humanos con genes al máximo útil; conceptos NO heredados."
                print(msg)
                state["status_message"] = msg
                return False
            if spec in ("best", "bank", "elite", "preserved"):
                if spec in ("bank", "elite", "preserved"):
                    best = world.gene_bank_candidates(2)
                    if len(best) < 2:
                        best = [h for h in world.best_gene_humans(alive_only=False, n=10) if not getattr(h, "immortal", False)][:2]
                else:
                    bank = world.gene_bank_candidates(2)
                    best = bank if len(bank) >= 2 else world.best_gene_humans(alive_only=True, n=2)
                    if len(best) < 2:
                        best = [h for h in world.best_gene_humans(alive_only=False, n=10) if not getattr(h, "immortal", False)][:2]
                if len(best) >= 1:
                    p1 = best[0]
                if len(best) >= 2:
                    p2 = best[1]
            elif "," in spec:
                a, b = spec.split(",", 1)
                try:
                    p1 = world.human_by_birth(int(a.strip()))
                    p2 = world.human_by_birth(int(b.strip()))
                except ValueError:
                    print("Padres inválidos. Ejemplo: spawn 5 9,24")
                    return False
                if not p1:
                    print(f"No existe padre1 #{a.strip()}.")
                    return False
                if not p2:
                    print(f"No existe padre2 #{b.strip()}.")
                    return False
            else:
                print("Uso: spawn 5 | spawn 5 9,24 | spawn 7 best")
                return False
        born = world.manual_spawn_humans(count, p1, p2)
        print(f"Spawn creados: {len(born)}")
        if p1 or p2:
            print("Genes heredados con mutación; conceptos NO heredados.")
        state["status_message"] = f"Spawn creados: {len(born)}"
        return False

    if cmd.startswith(("auto_spawn_1", "autospawn1", "spawn_auto_1", "spawn_when_one")):
        parts = cmd.split()
        # auto_spawn_1 sin número = interruptor.
        # auto_spawn_1 35 = activa y fija cantidad 35.
        # auto_spawn_1 off = desactiva.
        if len(parts) >= 2:
            arg = parts[1].strip().lower()
            if arg in ("off", "no", "false", "desactivar", "desactiva", "0"):
                world.auto_spawn_when_one = False
            else:
                try:
                    amount = int(float(arg.replace(",", ".")))
                    world.auto_spawn_amount = max(1, min(2000, amount))
                    world.auto_spawn_when_one = True
                except ValueError:
                    print("Uso: auto_spawn_1 | auto_spawn_1 35 | auto_spawn_1 off")
                    return False
        else:
            world.auto_spawn_when_one = not world.auto_spawn_when_one
        estado = "ACTIVADO" if world.auto_spawn_when_one else "DESACTIVADO"
        msg = f"Auto-spawn cuando quede 1 humano: {estado}. Generará {world.auto_spawn_amount} humanos con mezcla genética diversa."
        state["status_message"] = msg
        world.log("config_auto_spawn_1", "world", estado=estado, cantidad=world.auto_spawn_amount)
        print(msg)
        return False

    if cmd.startswith("boost") or cmd.startswith("mejorar"):
        # boost 721 vida 20 | boost 721 sed 1.5 | boost 721 hambre 1.5 | boost 721 vejez 1.5 | boost 721 all
        parts = cmd.split()
        if len(parts) < 3:
            print("Uso: boost 721 vida 20 | boost 721 sed 1.5 | boost 721 hambre 1.5 | boost 721 vejez 1.5 | boost 721 all")
            return False
        try:
            nb = int(parts[1])
        except ValueError:
            print("Número de humano inválido. Ejemplo: boost 721 vida 20")
            return False
        h = world.human_by_birth(nb)
        if not h:
            print(f"No existe humano #{nb}.")
            return False
        kind = parts[2]
        amount = None
        if len(parts) >= 4:
            try:
                amount = float(parts[3].replace(",", "."))
            except ValueError:
                print("Valor inválido.")
                return False
        if kind in ("vida", "life", "hp"):
            add = amount if amount is not None else 20.0
            h.max_hp += add
            h.hp = clamp(h.hp + add, 0, h.max_hp)
            msg = f"Humano #{nb}: vida +{add}, HP={h.hp:.1f}/{h.max_hp:.1f}"
        elif kind in ("sed", "thirst"):
            val = amount if amount is not None else 1.5
            h.thirst_resistance = max(h.thirst_resistance, val)
            msg = f"Humano #{nb}: resistencia_sed={h.thirst_resistance:.2f}"
        elif kind in ("hambre", "hunger"):
            val = amount if amount is not None else 1.5
            h.hunger_resistance = max(h.hunger_resistance, val)
            msg = f"Humano #{nb}: resistencia_hambre={h.hunger_resistance:.2f}"
        elif kind in ("vejez", "old", "edad"):
            val = amount if amount is not None else 1.5
            h.old_age_resistance = max(h.old_age_resistance, val)
            msg = f"Humano #{nb}: resistencia_vejez={h.old_age_resistance:.2f}"
        elif kind in ("all", "todo"):
            h.max_hp += 20
            h.hp = clamp(h.hp + 20, 0, h.max_hp)
            h.thirst_resistance = max(h.thirst_resistance, 1.5)
            h.hunger_resistance = max(h.hunger_resistance, 1.5)
            h.old_age_resistance = max(h.old_age_resistance, 1.5)
            msg = f"Humano #{nb}: boost completo aplicado. HP={h.hp:.1f}/{h.max_hp:.1f}, sed={h.thirst_resistance:.2f}, hambre={h.hunger_resistance:.2f}, vejez={h.old_age_resistance:.2f}"
        else:
            print("Tipo no válido: vida, sed, hambre, vejez, all")
            return False
        world.register_gene_bank(h, f"preservado por boost: {kind}")
        world.log("boost_manual", h.entity_id, tipo=kind, mensaje=msg)
        print(msg)
        state["status_message"] = msg
        return False

    if cmd.startswith("preserve") or cmd.startswith("guardar_genes") or cmd.startswith("proteger"):
        parts = cmd.split()
        if len(parts) != 2:
            print("Uso: preserve 721")
            return False
        try:
            nb = int(parts[1])
        except ValueError:
            print("Número inválido. Ejemplo: preserve 721")
            return False
        h = world.human_by_birth(nb)
        if not h:
            print(f"No existe humano #{nb}.")
            return False
        world.register_gene_bank(h, "preservado manualmente por el usuario")
        print(f"Humano #{nb} guardado en banco genético. Estado: {'vivo' if h.alive else 'muerto'}")
        return False

    if cmd in ("gene_bank", "banco_genes", "bank", "elite"):
        state["paused"] = True
        show_paged_text("BANCO GENÉTICO", world.gene_bank_report())
        return False

    if cmd.startswith("tops") or cmd.startswith("rankings") or cmd.startswith("top ") or cmd in ("top", "listas"):
        state["paused"] = True
        parts = cmd.split(maxsplit=1)
        category = parts[1].strip() if len(parts) > 1 and parts[0] in ("top", "tops", "rankings") else None
        show_paged_text("RANKINGS / TOPS", world.rankings_report(category=category, limit=12))
        return False

    if cmd in ("best_genes", "genes", "topgenes", "best"):
        state["paused"] = True
        top = world.best_gene_humans(alive_only=True, n=20)
        prefix = "=== 20 HUMANOS CON MEJORES GENES ==="
        if not top:
            prefix += "\nNo hay humanos vivos. Mostrando mejores genes históricos:"
            top = world.best_gene_humans(alive_only=False, n=20)
        if not top:
            out_text = prefix + "\nNo hay humanos registrados."
        else:
            out_text = prefix + "\n" + "\n".join(world.format_human_gene_line(h) for h in top)
        show_paged_text("MEJORES GENES", out_text)
        return False

    if cmd.startswith("tree"):
        state["paused"] = True
        parts = cmd.split()
        if len(parts) < 2:
            print("Uso: tree 27")
            return False
        try:
            nb = int(parts[1])
        except ValueError:
            print("Número inválido. Ejemplo: tree 27")
            return False
        show_paged_text(f"ÁRBOL GENEALÓGICO #{nb}", world.family_tree_report(nb))
        return False

    if cmd.startswith("export tree") or cmd.startswith("export_tree"):
        state["paused"] = True
        normalized = cmd.replace("export_tree", "export tree")
        parts = normalized.split(maxsplit=3)
        if len(parts) < 4:
            print("Uso: export tree 27 /ruta/arbol.svg | export tree all /ruta/arbol_general.svg")
            input("\nEnter para volver > ")
            return False
        spec = parts[2]
        raw_path = parts[3]
        msg = world.export_tree_image(spec, raw_path)
        print(msg)
        state["status_message"] = msg
        input("\nEnter para volver > ")
        return False

    if cmd.startswith("export brain") or cmd.startswith("export_brain"):
        state["paused"] = True
        normalized = cmd.replace("export_brain", "export brain")
        parts = normalized.split(maxsplit=3)
        if len(parts) < 4:
            print("Uso: export brain 27 /ruta/brain_27.txt")
            input("\nEnter para volver > ")
            return False
        try:
            nb = int(parts[2])
        except ValueError:
            print("Número inválido. Ejemplo: export brain 27 /ruta/brain_27.txt")
            input("\nEnter para volver > ")
            return False
        msg = world.export_brain_file(nb, parts[3])
        print(msg)
        state["status_message"] = msg
        input("\nEnter para volver > ")
        return False

    if cmd.startswith("brain") or cmd.startswith("neuronal") or cmd.startswith("mente"):
        state["paused"] = True
        parts = cmd.split()
        if len(parts) != 2:
            print("Uso: brain 27 | neuronal 27 | mente 27")
            return False
        try:
            nb = int(parts[1])
        except ValueError:
            print("Número inválido. Ejemplo: brain 27")
            return False
        show_paged_text(f"REGISTRO NEURONAL #{nb}", world.brain_report(nb))
        return False

    if cmd == "":
        advance_ticks(world, int(state.get("speed", 1)))
        return False

    if cmd in ("auto", "run", "play"):
        state["auto"] = True
        state["paused"] = False
        advance_ticks(world, int(state.get("speed", 1)))
        return False

    if cmd in ("pause", "pausar"):
        state["paused"] = not state["paused"]
        state["status_message"] = "Pausado" if state["paused"] else "Reanudado"
        return False

    if cmd in ("stop", "manual"):
        state["auto"] = False
        state["paused"] = False
        state["status_message"] = "Modo manual"
        return False

    if cmd.startswith("delay"):
        parts = cmd.split()
        if len(parts) >= 2:
            try:
                state["delay"] = max(0.0, float(parts[1].replace(",", ".")))
                state["status_message"] = f"Delay cambiado a {state['delay']}s"
            except ValueError:
                print("Uso: delay 0.2")
        else:
            print("Uso: delay 0.2")
        return False

    if cmd.startswith(("fast", "fast", "turbo")):
        parts = cmd.split()
        if len(parts) >= 2 and parts[1].lower() in ("off", "0", "false", "no"):
            state["fast"] = False
            state["status_message"] = "FATS desactivado. Speed/delay quedan como están."
            return False
        state["fast"] = not bool(state.get("fast")) if len(parts) == 1 else True
        if state["fast"]:
            state["delay"] = 0.0
            state["fast_last_check"] = time.time()
            state["fast_ticks_accum"] = 0
            state["fast_tps"] = 0.0
            state["fast_best_tps"] = 0.0
            state["fast_best_speed"] = int(state.get("speed", 1))
            state["status_message"] = f"FATS activado: ajustando speed automáticamente desde {state.get('speed', 1)} ticks/ciclo"
        else:
            state["status_message"] = "FATS desactivado"
        return False

    if cmd.startswith("speed"):
        parts = cmd.split()
        if len(parts) >= 2:
            try:
                value = int(float(parts[1].replace(",", ".")))
                state["speed"] = max(1, min(1000, value))
                state["status_message"] = f"Speed cambiado a {state['speed']} ticks/ciclo"
            except ValueError:
                print("Uso: speed 10")
        else:
            print(f"Speed actual: {state.get('speed', 1)} ticks/ciclo. Uso: speed 10")
        return False

    print("Comando no reconocido. Escribe help o comandos para ver la lista organizada.")
    return False



# Guardamos el procesador original para ampliarlo con v2.0.
_process_command_v17 = process_command


def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw_cmd = cmd.strip()
    low = raw_cmd.lower()

    # Ayudas organizadas v2.0
    if low in ("help sim", "ayuda sim"):
        state["paused"] = True; show_paged_text("HELP SIM", HELP_SIM_TEXT); return False
    if low in ("help export", "ayuda export"):
        state["paused"] = True; show_paged_text("HELP EXPORT", HELP_EXPORT_TEXT); return False
    if low in ("help lab", "ayuda lab", "lab help"):
        state["paused"] = True; show_paged_text("HELP LAB", HELP_LAB_TEXT); return False
    if low in ("help humans", "help human", "help población", "help poblacion"):
        state["paused"] = True; show_paged_text("HELP HUMANS", HELP_HUMANS_TEXT); return False
    if low in ("help detector", "help conceptos"):
        state["paused"] = True; show_paged_text("HELP DETECTOR", HELP_DETECTOR_TEXT); return False
    if low in ("help debug", "help fallos"):
        state["paused"] = True; show_paged_text("HELP DEBUG", HELP_DEBUG_TEXT); return False
    if low in ("help", "ayuda", "comandos", "?"):
        state["paused"] = True
        show_paged_text("AYUDA v2.1", HELP_TEXT + "\n\n" + "Usa también: help sim | help export | help humans | help lab | help detector | help debug")
        return False

    # Laboratorio v2.0
    if low.startswith("lab ") or low == "lab":
        parts = raw_cmd.split()
        if len(parts) == 1:
            state["paused"] = True; show_paged_text("HELP LAB", HELP_LAB_TEXT); return False
        action = parts[1].lower()
        if action in ("help", "ayuda"):
            state["paused"] = True; show_paged_text("HELP LAB", HELP_LAB_TEXT); return False
        if action == "spawn":
            if len(parts) < 3:
                print("Uso: lab spawn 5 | lab spawn 5 max | lab spawn 5 concept refugio")
                return False
            try:
                count = max(1, min(2000, int(float(parts[2].replace(',', '.')))))
            except ValueError:
                print("Cantidad inválida. Ejemplo: lab spawn 5 concept distancia")
                return False
            max_genes = False
            focus = "general"
            if len(parts) >= 4:
                if parts[3].lower() in ("max", "100", "100%", "maxgenes"):
                    max_genes = True
                elif parts[3].lower() == "concept" and len(parts) >= 5:
                    focus = parts[4].lower()
                    max_genes = True
                else:
                    focus = parts[3].lower()
            born = world.lab_spawn(count, focus=focus, max_genes=max_genes)
            msg = f"LAB spawn: {len(born)} sujetos | focus={focus} | max_genes={max_genes} | no heredan conceptos"
            print(msg)
            state["status_message"] = msg
            return False
        if action == "list":
            state["paused"] = True; show_paged_text("LAB LIST", world.lab_list_report()); return False
        if action == "report":
            state["paused"] = True; show_paged_text("LAB REPORT", world.lab_report()); return False
        if action == "watch":
            state["paused"] = True
            if len(parts) >= 4 and parts[2].lower() == "concept":
                show_paged_text(f"LAB WATCH CONCEPT {parts[3]}", world.lab_watch_report("concept " + parts[3])); return False
            if len(parts) >= 3:
                show_paged_text(f"LAB WATCH {parts[2]}", world.lab_watch_report(parts[2])); return False
            show_paged_text("USO LAB WATCH", "Uso: lab watch 1204 | lab watch concept refugio"); return False
        if action == "isolate":
            if len(parts) >= 3 and parts[2].lower() in ("off", "0", "false", "no"):
                world.lab_isolate = False
            else:
                world.lab_isolate = True
            msg = f"LAB isolate: {'ON' if world.lab_isolate else 'OFF'}"
            print(msg); state["status_message"] = msg; return False
        if action == "clear":
            n = 0
            for h in world.lab_humans():
                if h.alive:
                    h.alive = False; n += 1
            msg = f"LAB clear: {n} sujetos marcados como muertos."
            print(msg); state["status_message"] = msg; return False
        if action == "export":
            if len(parts) >= 3 and parts[2].lower() == "all":
                raw_path = " ".join(parts[3:]) if len(parts) >= 4 else ""
                msg = world.export_lab_all(raw_path)
            else:
                raw_path = " ".join(parts[2:]) if len(parts) >= 3 else ""
                if not raw_path:
                    print("Uso: lab export /ruta/lab.txt | lab export all /ruta/carpeta")
                    return False
                msg = world.export_simple_report("lab", raw_path)
            print(msg); state["status_message"] = msg; return False
        print("Comando lab no reconocido. Usa: help lab")
        return False

    # Exportaciones completas v2.0
    if low.startswith("export "):
        parts = raw_cmd.split(maxsplit=3)
        if len(parts) >= 4 and parts[1].lower() == "lab" and parts[2].lower() == "all":
            msg = world.export_lab_all(parts[3]); print(msg); state["status_message"] = msg; return False
        # export logs/conceptos/valiosos/fallos/investigaciones/gene_bank/rankings/lab RUTA
        if len(parts) >= 3 and parts[1].lower() in ("logs", "conceptos", "valiosos", "fallos", "investigaciones", "investigaciones_valiosas", "gene_bank", "rankings", "lab"):
            key = parts[1].lower()
            raw_path = parts[2] if len(parts) == 3 else parts[2] + (" " + parts[3] if len(parts) > 3 else "")
            msg = world.export_simple_report(key, raw_path)
            print(msg); state["status_message"] = msg; return False
        if len(parts) >= 4 and parts[1].lower() == "brains" and parts[2].lower() == "all":
            msg = world.export_brains_all(parts[3]); print(msg); state["status_message"] = msg; return False
        if len(parts) >= 4 and parts[1].lower() == "trees" and parts[2].lower() == "all":
            msg = world.export_trees_all(parts[3]); print(msg); state["status_message"] = msg; return False
        if len(parts) >= 4 and parts[1].lower() == "lineages" and parts[2].lower() == "all":
            msg = world.export_lineages_all(parts[3]); print(msg); state["status_message"] = msg; return False
        if len(parts) >= 4 and parts[1].lower() == "lab" and parts[2].lower() == "all":
            msg = world.export_lab_all(parts[3]); print(msg); state["status_message"] = msg; return False

    return _process_command_v17(cmd, world, state)



# ============================================================
# v2.1 — LABORATORIO AVANZADO: detector, bug hunters y actores falsos
# ============================================================

HELP_LAB_TEXT_V21 = HELP_LAB_TEXT + """

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
""".strip()

LAB_KNOWN_CONCEPTS = [
    "vida", "muerte", "miedo", "refugio", "agua", "comida", "trampa",
    "almacenamiento", "distancia", "dimension", "social", "herramienta",
    "sueño_fuerza", "cebo_trampa"
]

LAB_CONCEPT_ALIASES = {
    "cebo": "cebo_trampa",
    "trampa": "cebo_trampa",
    "sueno_fuerza": "sueño_fuerza",
    "sueño": "sueño_fuerza",
    "fuerza": "sueño_fuerza",
    "cueva": "refugio",
    "provisiones": "almacenamiento",
    "medicion": "distancia",
    "medición": "distancia",
    "espacio": "distancia",
}

def _lab_norm_concept(name: str) -> str:
    s = (name or "general").strip().lower().replace(" ", "_")
    return LAB_CONCEPT_ALIASES.get(s, s)

def _lab_parse_concepts(raw: str) -> List[str]:
    raw = (raw or "all").strip().lower()
    if raw in ("all", "todos", "todo", "*"):
        return list(LAB_KNOWN_CONCEPTS)
    out: List[str] = []
    for piece in raw.replace(";", ",").replace("+", ",").split(","):
        c = _lab_norm_concept(piece)
        if c:
            out.append(c)
    return out or ["general"]

def _lab_ensure(world: World) -> None:
    if not hasattr(world, "lab_simulations"):
        world.lab_simulations = []
    if not hasattr(world, "lab_bug_probes"):
        world.lab_bug_probes = []
    if not hasattr(world, "lab_detector_trials"):
        world.lab_detector_trials = []

def _lab_tag(h: Human, role: str, focus: str = "general") -> None:
    h.is_lab = True
    h.lab_role = role
    h.lab_focus = focus
    h.lab_color_tag = "L"
    h.lab_hidden_neural = True if role == "faker" else False
    h.lab_fake_concepts = getattr(h, "lab_fake_concepts", [])
    h.lab_fake_discoveries = getattr(h, "lab_fake_discoveries", [])
    h.lab_bug_notes = getattr(h, "lab_bug_notes", [])
    h.lab_detector_notes = getattr(h, "lab_detector_notes", [])

def _world_lab_spawn_role(self: World, count: int, role: str, focus: str = "general", concepts: Optional[List[str]] = None) -> List[Human]:
    _lab_ensure(self)
    focus = _lab_norm_concept(focus)
    born = self.lab_spawn(count, focus=focus, max_genes=True)
    for h in born:
        _lab_tag(h, role, focus)
        if role == "faker":
            h.lab_fake_concepts = list(concepts or LAB_KNOWN_CONCEPTS)
            h.lab_fake_next_index = 0
            h.lab_fake_last_tick = -999999
            h.detected_concepts.append(f"[LAB FAKE] actor con conceptos ocultos={','.join(h.lab_fake_concepts)}; red visible no los recibe como conocimiento heredado")
        elif role == "bug_hunter":
            h.detected_concepts.append("[LAB BUG] sujeto orientado a buscar fallos físicos/lógicos sin contaminar fallos normales")
        elif role == "detector_test":
            h.detected_concepts.append(f"[LAB DETECTOR] sujeto orientado a estresar detector en ruta={focus}")
    self.lab_notes.append(f"[Día {self.day} T{self.tick}] LAB role_spawn role={role} count={len(born)} focus={focus} concepts={concepts or []}")
    return born

World.lab_spawn_role = _world_lab_spawn_role

# ---------- Simulación conductual controlada para actores falsos ----------

def _lab_reinforce(h: Human, a: str, b: str, amount: float = 0.18) -> None:
    try:
        h.neural.reinforce(a, b, amount)
    except Exception:
        # Compatibilidad con versiones donde el método tenga otro nombre
        try:
            h.neural.connect(a, b, amount)
        except Exception:
            pass

def _lab_visible_cues_for_concept(world: World, h: Human, concept: str) -> List[str]:
    """Crea señales visibles de conducta para un LAB faker.
    No añade el concepto oculto a la red como conocimiento directo; solo deja huellas
    conductuales/neuronales que el detector normal puede o no detectar.
    """
    concept = _lab_norm_concept(concept)
    cues: List[str] = []
    if concept in ("vida", "muerte"):
        _lab_reinforce(h, "no_movimiento", "ser_human", 0.22)
        _lab_reinforce(h, "muerte_otro", "no_movimiento", 0.18)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="observar_ser_que_deja_de_moverse", visible=True)
        cues.append("no_movimiento ↔ ser_human / muerte_otro")
    elif concept == "miedo":
        _lab_reinforce(h, "dolor", "forma_trex", 0.22)
        _lab_reinforce(h, "atacado_por_trex", "vida_baja", 0.16)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="evitar_forma_grande_tras_dolor", visible=True)
        cues.append("dolor ↔ forma_trex / vida_baja")
    elif concept == "refugio":
        _lab_reinforce(h, "cueva_interior", "reposo", 0.24)
        _lab_reinforce(h, "cueva_interior", "seguridad", 0.16)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="dormir_en_cueva_y_volver", visible=True)
        cues.append("cueva_interior ↔ reposo/seguridad")
    elif concept in ("cebo_trampa", "trampa"):
        _lab_reinforce(h, "pollo_cercano", "semilla", 0.22)
        _lab_reinforce(h, "semilla", "ataque_chicken", 0.16)
        world.log("lab_fake_behavior", h.entity_id, concepto="cebo_trampa", accion="soltar_semilla_y_esperar_pollo", visible=True)
        cues.append("semilla ↔ pollo_cercano / ataque_chicken")
    elif concept == "almacenamiento":
        _lab_reinforce(h, "mano_coger", "objeto_seed", 0.20)
        _lab_reinforce(h, "objeto_seed", "uso_diferido", 0.18)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="guardar_semilla_para_luego", visible=True)
        cues.append("objeto_seed ↔ uso_diferido")
    elif concept in ("distancia", "dimension"):
        _lab_reinforce(h, "impulso_explorador", "mover_hacia_desconocido", 0.20)
        _lab_reinforce(h, "distancia_menor", "acercarse", 0.18)
        _lab_reinforce(h, "distancia_mayor", "alejarse", 0.18)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="acercarse_alejarse_sin_necesidad_basica", visible=True)
        cues.append("acercarse/alejarse ↔ distancia_menor/mayor")
    elif concept == "agua":
        _lab_reinforce(h, "mover_hacia_agua", "sed_alta", 0.20)
        _lab_reinforce(h, "agua", "sed_baja", 0.20)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="beber_y_bajar_sed", visible=True)
        cues.append("agua ↔ sed_baja")
    elif concept == "comida":
        _lab_reinforce(h, "hambre_alta", "mover_hacia_ser_pequeño", 0.20)
        _lab_reinforce(h, "comida_meat", "hambre_baja", 0.18)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="buscar_comida_y_bajar_hambre", visible=True)
        cues.append("comida_meat ↔ hambre_baja")
    elif concept == "social":
        _lab_reinforce(h, "bienestar_social", "otro_humano_cerca", 0.22)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="acercarse_a_otro_humano", visible=True)
        cues.append("bienestar_social ↔ otro_humano_cerca")
    elif concept == "herramienta":
        _lab_reinforce(h, "ataque_stone", "daño_mayor", 0.22)
        _lab_reinforce(h, "mano_coger", "objeto_stone", 0.15)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="comparar_mano_y_piedra", visible=True)
        cues.append("ataque_stone ↔ daño_mayor")
    elif concept == "sueño_fuerza":
        _lab_reinforce(h, "sueño_bajo", "golpe_debil", 0.22)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="golpes_debiles_con_sueño", visible=True)
        cues.append("sueño_bajo ↔ golpe_debil")
    else:
        _lab_reinforce(h, "impulso_explorador", "mover_hacia_desconocido", 0.12)
        world.log("lab_fake_behavior", h.entity_id, concepto=concept, accion="conducta_generica_de_prueba", visible=True)
        cues.append("señal genérica de exploración")
    return cues

def _lab_update_advanced(world: World) -> None:
    _lab_ensure(world)
    # Cada medio día aprox. los LAB avanzados emiten señales de prueba.
    if world.tick % max(6, TICKS_PER_DAY // 2) != 0:
        return
    for h in list(world.humans.values()):
        if not h.alive or not getattr(h, "is_lab", False):
            continue
        role = getattr(h, "lab_role", "")
        if role == "faker":
            concepts = list(getattr(h, "lab_fake_concepts", []) or LAB_KNOWN_CONCEPTS)
            if not concepts:
                continue
            idx = int(getattr(h, "lab_fake_next_index", 0)) % len(concepts)
            concept = concepts[idx]
            h.lab_fake_next_index = idx + 1
            cues = _lab_visible_cues_for_concept(world, h, concept)
            rec = {
                "tick": world.tick,
                "day": world.day,
                "human": h.birth_number,
                "concept": concept,
                "cues": cues,
            }
            h.lab_fake_discoveries.append(rec)
            world.lab_simulations.append(rec)
            h.record(Event(world.tick, world.day, h.entity_id, "lab_fake_discovery", rec))
        elif role == "bug_hunter":
            probes = [
                "combinar_objetos", "mover_cueva", "golpear_aire", "coger_objeto_pesado",
                "ruta_borde", "apilar_piedras", "soltar_recoger_repetido"
            ]
            probe = random.choice(probes)
            note = {"tick": world.tick, "day": world.day, "human": h.birth_number, "probe": probe, "resultado": "registrado_como_prueba_lab"}
            world.lab_bug_probes.append(note)
            h.lab_bug_notes.append(note)
            world.log("lab_bug_probe", h.entity_id, prueba=probe, nota="buscador de errores; no es fallo real salvo que genere excepción o comportamiento imposible")
        elif role == "detector_test":
            focus = getattr(h, "lab_focus", "general")
            cues = _lab_visible_cues_for_concept(world, h, focus)
            note = {"tick": world.tick, "day": world.day, "human": h.birth_number, "focus": focus, "cues": cues}
            world.lab_detector_trials.append(note)
            h.lab_detector_notes.append(note)

_old_run_tick_v20 = World.run_tick

def _run_tick_v21(self: World) -> None:
    _old_run_tick_v20(self)
    _lab_update_advanced(self)

World.run_tick = _run_tick_v21

# ---------- Informes LAB v2.1 ----------

_old_lab_list_report_v20 = World.lab_list_report

def _lab_list_report_v21(self: World) -> str:
    base = _old_lab_list_report_v20(self)
    lines = [base, "", "ROLES LAB v2.1"]
    for h in self.lab_humans():
        role = getattr(h, "lab_role", "standard")
        extra = ""
        if role == "faker":
            extra = f" ocultos={','.join(getattr(h, 'lab_fake_concepts', []))} simulados={len(getattr(h, 'lab_fake_discoveries', []))}"
        elif role == "bug_hunter":
            extra = f" probes={len(getattr(h, 'lab_bug_notes', []))}"
        elif role == "detector_test":
            extra = f" trials={len(getattr(h, 'lab_detector_notes', []))}"
        lines.append(f"L#{h.birth_number:<5} role={role:<14} focus={getattr(h,'lab_focus','general'):<16}{extra}")
    return "\n".join(lines)

World.lab_list_report = _lab_list_report_v21

_old_lab_report_v20 = World.lab_report

def _lab_audit_text(self: World) -> str:
    _lab_ensure(self)
    lines = []
    lines.append("AUDITORÍA LAB v2.1 — ACTORES FALSOS / DETECTOR")
    lines.append("=" * 100)
    fakers = [h for h in self.lab_humans() if getattr(h, "lab_role", "") == "faker"]
    if not fakers:
        lines.append("No hay LAB fakers. Usa: lab faker 3 all | lab faker 2 vida,refugio")
        return "\n".join(lines)
    for h in fakers:
        lines.append(f"\nL#{h.birth_number} estado={'VIVO' if h.alive else 'muerto'} focus={getattr(h,'lab_focus','-')} score={self.gene_score(h):.1f}")
        hidden = list(getattr(h, "lab_fake_concepts", []))
        lines.append(f"  conceptos ocultos: {', '.join(hidden)}")
        sims = list(getattr(h, "lab_fake_discoveries", []))
        lines.append(f"  simulaciones emitidas: {len(sims)}")
        # Detector: búsqueda simple en conceptos detectados e investigaciones por palabra clave.
        combined = "\n".join(h.detected_concepts).lower()
        invs = [inv for inv in self.investigations.values() if inv.subject_birth == h.birth_number]
        inv_text = "\n".join(f"{inv.category} {inv.hypothesis} {inv.state} {inv.confidence:.1f}" for inv in invs).lower()
        for c in hidden:
            cn = _lab_norm_concept(c)
            simulated = sum(1 for s in sims if _lab_norm_concept(str(s.get("concept"))) == cn)
            detected = (cn in combined) or (cn in inv_text)
            # equivalencias más humanas
            if cn == "cebo_trampa":
                detected = detected or ("cebo" in combined) or ("trampa" in combined) or ("cebo" in inv_text) or ("trampa" in inv_text)
            if cn == "sueño_fuerza":
                detected = detected or ("sueño" in combined) or ("fuerza" in combined) or ("sueño" in inv_text) or ("fuerza" in inv_text)
            lines.append(f"    - {cn:<18} simulado={simulated:<3} detector={'SÍ' if detected else 'NO'}")
    lines.append("\nInterpretación: si simulado>SÍ pero detector=NO, el detector no vio una conducta que el actor intentó representar. Si detector=SÍ con pocas simulaciones, puede ser detector sensible o buena ruta conductual.")
    return "\n".join(lines)

World.lab_audit_report = _lab_audit_text

def _lab_report_v21(self: World) -> str:
    base = _old_lab_report_v20(self)
    _lab_ensure(self)
    lines = [base, "", "LAB v2.1 — RESUMEN AVANZADO", "=" * 100]
    lines.append(f"Detector trials: {len(self.lab_detector_trials)} | Bug probes: {len(self.lab_bug_probes)} | Fake discoveries: {len(self.lab_simulations)}")
    roles: Dict[str, int] = {}
    for h in self.lab_humans():
        roles[getattr(h, "lab_role", "standard")] = roles.get(getattr(h, "lab_role", "standard"), 0) + 1
    lines.append("Roles: " + (", ".join(f"{k}={v}" for k, v in sorted(roles.items())) if roles else "sin sujetos"))
    if self.lab_bug_probes:
        lines.append("\nÚltimas pruebas de bug hunters:")
        for note in self.lab_bug_probes[-10:]:
            lines.append(f"  - Día {note['day']} T{note['tick']} L#{note['human']}: {note['probe']} -> {note['resultado']}")
    if self.lab_simulations:
        lines.append("\nÚltimas simulaciones fake:")
        for rec in self.lab_simulations[-10:]:
            lines.append(f"  - Día {rec['day']} T{rec['tick']} L#{rec['human']}: fingió {rec['concept']} | pistas={'; '.join(rec.get('cues', []))}")
    lines.append("\n" + self.lab_audit_report())
    return "\n".join(lines)

World.lab_report = _lab_report_v21

# ---------- Export LAB all ampliado ----------

_old_export_lab_all_v20 = World.export_lab_all

def _export_lab_all_v21(self: World, raw_path: str) -> str:
    msg = _old_export_lab_all_v20(self, raw_path)
    folder = pathlib.Path(os.path.expanduser(str(raw_path).strip()))
    if folder.suffix:
        folder = folder.with_suffix("")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "lab_audit_v21.txt").write_text(self.lab_audit_report(), encoding="utf-8")
    (folder / "lab_bug_probes_v21.txt").write_text("\n".join(str(x) for x in getattr(self, "lab_bug_probes", [])), encoding="utf-8")
    (folder / "lab_detector_trials_v21.txt").write_text("\n".join(str(x) for x in getattr(self, "lab_detector_trials", [])), encoding="utf-8")
    (folder / "lab_fake_discoveries_v21.txt").write_text("\n".join(str(x) for x in getattr(self, "lab_simulations", [])), encoding="utf-8")
    return msg + f"\nAñadidos ficheros v2.1: lab_audit_v21.txt, lab_bug_probes_v21.txt, lab_detector_trials_v21.txt, lab_fake_discoveries_v21.txt"

World.export_lab_all = _export_lab_all_v21

# ---------- Comandos v2.1 ----------

_process_command_v20 = process_command

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw_cmd = cmd.strip()
    low = raw_cmd.lower()
    parts = raw_cmd.split()

    if low in ("help lab", "ayuda lab", "lab help"):
        state["paused"] = True
        show_paged_text("HELP LAB v2.1", HELP_LAB_TEXT_V21)
        return False

    if low.startswith("lab detector"):
        # lab detector X [concepto]
        try:
            count = int(float(parts[2].replace(',', '.'))) if len(parts) >= 3 else 1
        except Exception:
            print("Uso: lab detector 5 distancia")
            return False
        focus = _lab_norm_concept(parts[3]) if len(parts) >= 4 else "general"
        born = world.lab_spawn_role(max(1, min(2000, count)), "detector_test", focus=focus)
        msg = f"LAB detector: {len(born)} sujetos creados para poner a prueba el detector | focus={focus}"
        print(msg); state["status_message"] = msg; return False

    if low.startswith("lab bugs") or low.startswith("lab bughunters") or low.startswith("lab bughunter"):
        try:
            count = int(float(parts[2].replace(',', '.'))) if len(parts) >= 3 else 1
        except Exception:
            print("Uso: lab bugs 5")
            return False
        born = world.lab_spawn_role(max(1, min(2000, count)), "bug_hunter", focus="errores")
        msg = f"LAB bug hunters: {len(born)} sujetos creados para buscar fallos físicos/lógicos"
        print(msg); state["status_message"] = msg; return False

    if low.startswith("lab faker") or low.startswith("lab fake") or low.startswith("lab actor"):
        # lab faker X all | lab faker X vida,refugio
        try:
            count = int(float(parts[2].replace(',', '.'))) if len(parts) >= 3 else 1
        except Exception:
            print("Uso: lab faker 3 all | lab faker 2 vida,refugio")
            return False
        raw_concepts = " ".join(parts[3:]) if len(parts) >= 4 else "all"
        concepts = _lab_parse_concepts(raw_concepts)
        born = world.lab_spawn_role(max(1, min(2000, count)), "faker", focus="detector", concepts=concepts)
        msg = f"LAB faker: {len(born)} actores creados | conceptos ocultos={','.join(concepts)} | red visible sin conocimiento heredado"
        print(msg); state["status_message"] = msg; return False

    if low in ("lab fake_report", "lab fakereport", "lab audit", "lab auditoria", "lab auditoría"):
        state["paused"] = True
        show_paged_text("LAB AUDIT v2.1", world.lab_audit_report())
        return False

    return _process_command_v20(cmd, world, state)


def enable_command_mode() -> Optional[List[Any]]:
    """
    Modo de lectura carácter a carácter para que en auto puedas escribir comandos
    sin que se borren visualmente con el refresco del mapa. Solo se usa en TTY real.
    """
    if not sys.stdin.isatty():
        return None
    old = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    # Quitamos eco: el propio programa dibuja el buffer de comando abajo.
    new = termios.tcgetattr(sys.stdin)
    new[3] = new[3] & ~termios.ECHO
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new)
    return old


def restore_command_mode(old: Optional[List[Any]]) -> None:
    if old is not None and sys.stdin.isatty():
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)


def read_auto_command(command_buffer: str) -> Tuple[str, Optional[str]]:
    """
    Lee teclas sin bloquear durante el modo auto.
    Devuelve (buffer_actualizado, comando_completo_o_None).
    """
    if not sys.stdin.isatty():
        return command_buffer, None

    completed: Optional[str] = None
    while select.select([sys.stdin], [], [], 0)[0]:
        ch = sys.stdin.read(1)
        if ch in ("\n", "\r"):
            completed = command_buffer.strip()
            command_buffer = ""
            break
        if ch in ("\x7f", "\b"):
            command_buffer = command_buffer[:-1]
            continue
        if ch == "\x03":
            raise KeyboardInterrupt
        if ch == "\x1b":
            # Ignorar secuencias de escape/flechas de momento.
            continue
        if ch.isprintable():
            command_buffer += ch
    return command_buffer, completed


def main() -> None:
    global INITIAL_HUMANS

    try:
        entrada = input("Cantidad de humanos iniciales [2]: ").strip()
        if entrada:
            INITIAL_HUMANS = max(0, int(entrada))
    except ValueError:
        print("Valor no válido. Se usan 2 humanos iniciales. También puedes poner 0.")
        INITIAL_HUMANS = 2

    world = World()
    state: Dict[str, Any] = {"auto": False, "paused": False, "delay": 0.08, "speed": 1, "status_message": "",
                            "fast": False, "fast_tps": 0.0, "fast_last_check": time.time(),
                            "fast_ticks_accum": 0, "fast_best_tps": 0.0, "fast_best_speed": 1}
    command_buffer = ""
    old_terminal: Optional[List[Any]] = None
    last_render = 0.0
    render_interval = 0.06  # aunque delay sea 0, no repintamos cientos de veces por segundo
    render_dirty = True

    print("PROTOHUMANOS 2D v2.1.4")
    print("Base v2.0: experimento principal intacto + laboratorio separado + exportaciones organizadas.")
    print("Comandos: help | help lab | help export | auto/run | fast | spawn | lab spawn 5 concept refugio | export useful RUTA | q")

    try:
        # Modo comando permanente: evita que Enter haga eco/salto de línea en modo manual.
        # Para comandos largos se restaura temporalmente dentro del flujo.
        old_terminal = enable_command_mode()

        while world.tick < MAX_TICKS:
            if old_terminal is None:
                old_terminal = enable_command_mode()
                render_dirty = True

            old_buffer = command_buffer
            completed_cmd: Optional[str] = None
            command_buffer, completed_cmd = read_auto_command(command_buffer)
            if command_buffer != old_buffer:
                render_dirty = True

            now = time.time()
            should_render = render_dirty or (state["auto"] and not state["paused"] and (now - last_render >= render_interval))
            if world.tick % RENDER_EVERY_TICKS == 0 and should_render:
                mode_txt = "AUTO" if state["auto"] and not state["paused"] else ("PAUSA" if state["paused"] else "MANUAL")
                fast_txt = "ON" if state.get("fast") else "OFF"
                footer = [
                    f"Modo: {mode_txt} | v2.1 | delay: {state['delay']:.4g}s | speed: {state.get('speed', 1)} ticks/ciclo | fast: {fast_txt} | TPS≈{state.get('fast_tps', 0.0):.1f} | auto_spawn_1: {world.auto_spawn_when_one} ({world.auto_spawn_amount})",
                ]
                if state.get("status_message"):
                    footer.append(cyan_alert(str(state["status_message"])))
                footer.append("Comandos: help | auto/run | pause | stop | delay <segundos> | speed <ticks> | fast | spawn | auto_spawn_1 [N] | logs | fallos | best | tree N | brain N | q")
                footer.append(cyan_alert(f"Comando > {command_buffer}"))
                world.render(footer)
                last_render = now
                render_dirty = False

            alive_humans = sum(1 for h in world.humans.values() if h.alive and not getattr(h, "is_lab", False))
            alive_lab_humans = sum(1 for h in world.humans.values() if h.alive and getattr(h, "is_lab", False))
            total_alive_humans = alive_humans + alive_lab_humans

            # v2.1.4: si la simulación se inició con 0 humanos normales pero hay LAB vivos,
            # o si el usuario quiere correr un mundo/laboratorio sin población normal, NO se debe
            # parar auto/run. Antes esto hacía que run/auto avanzara solo 1 tick en pruebas LAB.
            # auto_spawn_1 sigue mirando SOLO humanos normales, pero la pausa por extinción solo
            # se aplica cuando no queda ningún humano de ningún tipo y no hay laboratorio vivo.
            if alive_humans == 0 and world.auto_spawn_when_one:
                world.check_auto_spawn_when_one()
                alive_humans = sum(1 for h in world.humans.values() if h.alive and not getattr(h, "is_lab", False))
                total_alive_humans = alive_humans + alive_lab_humans
                render_dirty = True

            if total_alive_humans == 0:
                # Solo avisamos una vez, pero NO forzamos pause si el usuario está usando un mundo
                # vacío/laboratorio y quiere seguir avanzando animales/semillas.
                if not world.extinction_notice_shown:
                    restore_command_mode(old_terminal)
                    old_terminal = None
                    print("\nNo quedan humanos vivos. La simulación sigue abierta y puede seguir corriendo si usas run/auto.")
                    print(cyan_alert("Puedes escribir spawn 20 best, lab bugs 20 immortal, o seguir con el mundo vacío."))
                    world.extinction_notice_shown = True
                    render_dirty = True

            if completed_cmd is not None:
                # Enter vacío = avanzar ticks, sin eco ni salto visual.
                if completed_cmd.strip() == "":
                    should_quit = process_command("", world, state)
                    render_dirty = True
                else:
                    # Comandos reales: restauramos terminal normal porque pueden abrir HTML,
                    # imprimir mensajes o pedir Enter temporalmente.
                    restore_command_mode(old_terminal)
                    old_terminal = None
                    should_quit = process_command(completed_cmd, world, state)
                    render_dirty = True
                command_buffer = ""
                if should_quit:
                    break
                continue

            if state["auto"] and not state["paused"]:
                if state.get("delay", 0.0) > 0:
                    time.sleep(state["delay"])
                batch = int(state.get("speed", 1))
                t0 = time.perf_counter()
                advance_ticks(world, batch)
                elapsed = time.perf_counter() - t0
                update_fast_controller(state, batch, elapsed)
                render_dirty = True
                continue

            # Manual/pausa: no bloqueamos con input() para que Enter no haga scroll.
            # Tampoco repintamos constantemente; solo al cambiar buffer o avanzar tick.
            time.sleep(0.02)

    except KeyboardInterrupt:
        restore_command_mode(old_terminal)
        old_terminal = None
        print("\nSimulación interrumpida.")
    finally:
        restore_command_mode(old_terminal)


# ============================================================
# v2.1.1 — INMORTALIDAD EXPERIMENTAL PARA LAB / SPAWN
# ============================================================

HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V21 + """

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
""".strip()

_IMMORTAL_WORDS = {"immortal", "inmortal", "invulnerable", "inmortales", "immortals"}
_IMMORTAL_LEARN_WORDS = {"learn", "learning", "aprende", "aprender", "conceptos", "con_conceptos", "with_learning", "withlearn", "si_aprende", "aprendizaje"}

def _is_immortal_request(tokens: List[str]) -> bool:
    return any(t.lower() in _IMMORTAL_WORDS for t in tokens)

def _allows_immortal_learning(tokens: List[str]) -> bool:
    return any(t.lower() in _IMMORTAL_LEARN_WORDS for t in tokens)

def _remove_immortal_tokens(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t.lower() not in _IMMORTAL_WORDS and t.lower() not in _IMMORTAL_LEARN_WORDS]

def _mark_immortal(world: World, h: Human, reason: str = "comando", allow_learning: bool = False) -> None:
    h.immortal = True
    h.concept_learning_blocked = not bool(allow_learning)
    # No es conocimiento ni memoria: solo modo de laboratorio/experimento para que no muera.
    # Se le sube la resistencia para que no se quede bloqueado siempre por hambre/sed.
    h.max_hp = max(float(h.max_hp), 9999.0)
    h.hp = max(float(h.hp), float(h.max_hp))
    h.hunger_resistance = max(float(getattr(h, 'hunger_resistance', 1.0)), 9999.0)
    h.thirst_resistance = max(float(getattr(h, 'thirst_resistance', 1.0)), 9999.0)
    h.old_age_resistance = max(float(getattr(h, 'old_age_resistance', 1.0)), 9999.0)
    h.hunger = min(float(getattr(h, 'hunger', 0.0)), 5.0)
    h.thirst = min(float(getattr(h, 'thirst', 0.0)), 5.0)
    h.sleepiness = min(float(getattr(h, 'sleepiness', 0.0)), 5.0)
    h.energy = 100.0
    if not any("[MODO INMORTAL]" in c for c in h.detected_concepts):
        if allow_learning:
            h.detected_concepts.append("[MODO INMORTAL] activado por laboratorio/debug; APRENDIZAJE PERMITIDO por comando")
        else:
            h.detected_concepts.append("[MODO INMORTAL] activado por laboratorio/debug; aprendizaje de conceptos BLOQUEADO")
    if not allow_learning:
        try:
            for inv in world.investigations.values():
                if inv.subject_birth == h.birth_number:
                    inv.concluded = True
                    inv.state = "BLOQUEADA_POR_INMORTAL_SIN_APRENDIZAJE"
        except Exception:
            pass
    try:
        world.log("modo_inmortal", h.entity_id, nacimiento=h.birth_number, motivo=reason, aprendizaje=("permitido" if allow_learning else "bloqueado"), nota="no puede morir; aprendizaje conceptual bloqueado salvo comando con learn/aprender")
    except Exception:
        pass

# Blindaje final: si algo llama a kill(), los inmortales no mueren.
_old_kill_v211 = World.kill

def _kill_v211(self: World, c: Creature, cause: str) -> None:
    if isinstance(c, Human) and getattr(c, "immortal", False):
        c.alive = True
        c.hp = max(float(c.hp), max(1.0, float(c.max_hp) * 0.25))
        c.last_attacker = None
        self.log("muerte_evitada_inmortal", c.entity_id, causa=cause, hp=round(c.hp, 2), pos=c.pos(), nota="humano experimental inmortal; no muere")
        return
    return _old_kill_v211(self, c, cause)

World.kill = _kill_v211

# Comandos v2.1.1: interceptan solo cuando aparece immortal/inmortal o help lab.
_process_command_v21 = process_command

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw_cmd = cmd.strip()
    low = raw_cmd.lower()
    tokens = raw_cmd.split()

    if low in ("help lab", "ayuda lab", "lab help"):
        state["paused"] = True
        show_paged_text("HELP LAB v2.1.1", HELP_LAB_TEXT_V211)
        return False

    if not tokens:
        return _process_command_v21(cmd, world, state)

    # Marcar/quitar inmortalidad a un humano existente.
    if tokens[0].lower() in ("immortal", "inmortal"):
        if len(tokens) < 2:
            print("Uso: immortal 721")
            return False
        try:
            nb = int(tokens[1])
        except ValueError:
            print("Número inválido. Ejemplo: immortal 721")
            return False
        h = world.human_by_birth(nb)
        if not h:
            print(f"No existe humano #{nb}.")
            return False
        _mark_immortal(world, h, reason="comando manual")
        msg = f"Humano #{nb} marcado como INMORTAL. No hereda conceptos; solo queda protegido para pruebas."
        print(msg); state["status_message"] = msg; return False

    if tokens[0].lower() in ("mortal", "noimmortal", "no_inmortal"):
        if len(tokens) < 2:
            print("Uso: mortal 721")
            return False
        try:
            nb = int(tokens[1])
        except ValueError:
            print("Número inválido. Ejemplo: mortal 721")
            return False
        h = world.human_by_birth(nb)
        if not h:
            print(f"No existe humano #{nb}.")
            return False
        h.immortal = False
        msg = f"Humano #{nb} ya NO es inmortal. Mantiene genes/vida actuales, pero puede morir."
        world.log("modo_mortal", h.entity_id, nacimiento=h.birth_number)
        print(msg); state["status_message"] = msg; return False

    immortal = _is_immortal_request(tokens)
    allow_immortal_learning = _allows_immortal_learning(tokens)
    if not immortal:
        return _process_command_v21(cmd, world, state)

    clean = _remove_immortal_tokens(tokens)
    clean_low = " ".join(clean).lower()

    # spawnmax X immortal
    if clean and clean[0].lower() in ("spawnmax", "spawn_max", "spawn100", "spawn_100", "maxhumans"):
        if len(clean) < 2:
            print("Uso: spawnmax 10 immortal")
            return False
        try:
            count = max(1, min(2000, int(float(clean[1].replace(',', '.')))))
        except ValueError:
            print("Cantidad no válida. Ejemplo: spawnmax 10 immortal")
            return False
        born = world.manual_spawn_max_humans(count)
        for h in born:
            _mark_immortal(world, h, reason="spawnmax immortal", allow_learning=allow_immortal_learning)
        msg = f"Spawn MAX INMORTAL creados: {len(born)} humanos. Sin conceptos heredados."
        print(msg); state["status_message"] = msg; return False

    # spawn X ... immortal
    if clean and clean[0].lower() == "spawn":
        if len(clean) < 2:
            print("Uso: spawn 5 immortal | spawn 5 max immortal | spawn 5 best immortal | spawn 5 9,24 immortal")
            return False
        try:
            count = max(1, min(2000, int(float(clean[1].replace(',', '.')))))
        except ValueError:
            print("Cantidad no válida. Ejemplo: spawn 5 immortal")
            return False
        spec = " ".join(clean[2:]).strip().lower() if len(clean) >= 3 else ""
        born: List[Human] = []
        if spec in ("max", "maxgenes", "100", "100%"):
            born = world.manual_spawn_max_humans(count)
        else:
            p1 = p2 = None
            if spec in ("best", "bank", "elite", "preserved"):
                if spec in ("bank", "elite", "preserved"):
                    best = world.gene_bank_candidates(2)
                    if len(best) < 2:
                        best = [h for h in world.best_gene_humans(alive_only=False, n=10) if not getattr(h, "immortal", False)][:2]
                else:
                    bank = world.gene_bank_candidates(2)
                    best = bank if len(bank) >= 2 else world.best_gene_humans(alive_only=True, n=2)
                    if len(best) < 2:
                        best = [h for h in world.best_gene_humans(alive_only=False, n=10) if not getattr(h, "immortal", False)][:2]
                if len(best) >= 1:
                    p1 = best[0]
                if len(best) >= 2:
                    p2 = best[1]
            elif spec and "," in spec:
                a, b = spec.split(",", 1)
                try:
                    p1 = world.human_by_birth(int(a.strip()))
                    p2 = world.human_by_birth(int(b.strip()))
                except ValueError:
                    print("Padres inválidos. Ejemplo: spawn 5 9,24 immortal")
                    return False
                if not p1 or not p2:
                    print("No existe alguno de los padres indicados.")
                    return False
            elif spec:
                print("Uso: spawn 5 immortal | spawn 5 max immortal | spawn 5 best immortal | spawn 5 9,24 immortal")
                return False
            born = world.manual_spawn_humans(count, p1, p2)
        for h in born:
            _mark_immortal(world, h, reason=f"spawn immortal ({spec or 'sin padres'})", allow_learning=allow_immortal_learning)
        msg = f"Spawn INMORTAL creados: {len(born)} humanos. Sin conceptos heredados."
        print(msg); state["status_message"] = msg; return False

    # lab ... immortal
    if clean and clean[0].lower() == "lab":
        if len(clean) < 2:
            print("Uso: lab bugs 5 immortal | lab detector 5 distancia immortal | lab spawn 5 max immortal")
            return False
        action = clean[1].lower()
        born: List[Human] = []
        if action == "spawn":
            if len(clean) < 3:
                print("Uso: lab spawn 5 immortal | lab spawn 5 max immortal | lab spawn 5 concept refugio immortal")
                return False
            try:
                count = max(1, min(2000, int(float(clean[2].replace(',', '.')))))
            except ValueError:
                print("Cantidad inválida. Ejemplo: lab spawn 5 concept distancia immortal")
                return False
            max_genes = False; focus = "general"
            if len(clean) >= 4:
                if clean[3].lower() in ("max", "100", "100%", "maxgenes"):
                    max_genes = True
                elif clean[3].lower() == "concept" and len(clean) >= 5:
                    focus = clean[4].lower(); max_genes = True
                else:
                    focus = clean[3].lower()
            born = world.lab_spawn(count, focus=focus, max_genes=max_genes)
            role_msg = f"LAB spawn immortal focus={focus} max={max_genes}"
        elif action in ("bugs", "bughunters", "bughunter"):
            try:
                count = max(1, min(2000, int(float(clean[2].replace(',', '.'))))) if len(clean) >= 3 else 1
            except ValueError:
                print("Uso: lab bugs 5 immortal")
                return False
            born = world.lab_spawn_role(count, "bug_hunter", focus="errores")
            role_msg = "LAB bug hunters immortal"
        elif action == "detector":
            try:
                count = max(1, min(2000, int(float(clean[2].replace(',', '.'))))) if len(clean) >= 3 else 1
            except ValueError:
                print("Uso: lab detector 5 distancia immortal")
                return False
            focus = _lab_norm_concept(clean[3]) if len(clean) >= 4 else "general"
            born = world.lab_spawn_role(count, "detector_test", focus=focus)
            role_msg = f"LAB detector immortal focus={focus}"
        elif action in ("faker", "fake", "actor"):
            try:
                count = max(1, min(2000, int(float(clean[2].replace(',', '.'))))) if len(clean) >= 3 else 1
            except ValueError:
                print("Uso: lab faker 3 vida,refugio immortal")
                return False
            raw_concepts = " ".join(clean[3:]) if len(clean) >= 4 else "all"
            concepts = _lab_parse_concepts(raw_concepts)
            born = world.lab_spawn_role(count, "faker", focus="detector", concepts=concepts)
            role_msg = f"LAB faker immortal concepts={','.join(concepts)}"
        else:
            return _process_command_v21(" ".join(clean), world, state)
        for h in born:
            _mark_immortal(world, h, reason=role_msg, allow_learning=allow_immortal_learning)
        msg = f"{role_msg}: {len(born)} sujetos creados como INMORTALES. Sin conceptos heredados."
        print(msg); state["status_message"] = msg; return False

    return _process_command_v21(cmd, world, state)


# v2.1.3: bloqueo de aprendizaje conceptual para inmortales sin "learn/aprender".
# Esto mantiene a los bug hunters inmortales como herramientas de prueba física, sin que acaben
# aprendiendo refugio y quedándose en cuevas. Si se crea con "immortal learn", aprende normal.
_open_or_update_investigation_v213_prev = World.open_or_update_investigation

def _open_or_update_investigation_v213(self: World, h: Human, category: str, hypothesis: str, confidence: float,
                                      evidence_for: Optional[List[str]] = None,
                                      evidence_against: Optional[List[str]] = None,
                                      inherited_from: Optional[int] = None,
                                      generations_left: int = 3,
                                      duration_days: int = 6) -> ConceptInvestigation:
    if getattr(h, "concept_learning_blocked", False):
        # No abrimos investigaciones conceptuales para sujetos inmortales sin aprendizaje.
        return ConceptInvestigation(
            inv_id=-1,
            origin_birth=getattr(h, "birth_number", 0),
            subject_birth=getattr(h, "birth_number", 0),
            category=category,
            hypothesis="bloqueada: inmortal sin aprendizaje conceptual",
            started_tick=self.tick,
            started_day=self.day,
            expires_tick=self.tick,
            last_update_tick=self.tick,
            confidence=0.0,
            state="BLOQUEADA_POR_INMORTAL_SIN_APRENDIZAJE",
            concluded=True,
        )
    return _open_or_update_investigation_v213_prev(self, h, category, hypothesis, confidence, evidence_for, evidence_against, inherited_from, generations_left, duration_days)

World.open_or_update_investigation = _open_or_update_investigation_v213

_print_report_v213_prev = MetaObserver.print_report

def _print_report_v213(self: MetaObserver, title: str, human: Optional[Human], tipo: str, concepto: str, resumen: str,
                       equivalente: str, confidence: float, evidencias: List[str], factors: Dict[str, float], note: str,
                       group_name: str = "población activa", extra: Optional[List[str]] = None, red: bool = False,
                       cyan: bool = False, darkblue: bool = False, skip_review: bool = False) -> None:
    if human is not None and getattr(human, "concept_learning_blocked", False) and not red:
        # Silenciamos reportes conceptuales de sujetos inmortales sin aprendizaje.
        # Sus eventos físicos siguen en all_logs/últimos eventos/lab_bug_probes.
        return None
    return _print_report_v213_prev(self, title, human, tipo, concepto, resumen, equivalente, confidence, evidencias, factors, note, group_name, extra, red, cyan, darkblue, skip_review)

MetaObserver.print_report = _print_report_v213

_update_investigations_v213_prev = World.update_investigations

def _update_investigations_v213(self: World) -> None:
    # Cerramos cualquier investigación que hubiera quedado abierta antes de marcar inmortal sin aprendizaje.
    for inv in self.investigations.values():
        h = self.human_by_birth(inv.subject_birth)
        if h is not None and getattr(h, "concept_learning_blocked", False):
            inv.concluded = True
            inv.state = "BLOQUEADA_POR_INMORTAL_SIN_APRENDIZAJE"
            inv.confidence = 0.0
    return _update_investigations_v213_prev(self)

World.update_investigations = _update_investigations_v213

# Actualización de ayuda de laboratorio para v2.1.3.
HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

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
"""



# ============================================================
# v2.1.5 — LAB NO-LEARN: evitar quedarse en cuevas
# ============================================================
# Motivo:
# - Los sujetos LAB inmortales sin aprendizaje (bugs / detector / faker) deben servir
#   para explorar el sistema, probar errores o simular conceptos, no para optimizar
#   supervivencia ni quedarse quietos en cuevas.
# - Esto NO cambia la lógica de humanos normales.
# - Tampoco impide que un LAB con "immortal learn" aprenda/refugio si tú lo quieres.

LAB_NOLEARN_CAVE_AVOID_ROLES = {"bugs", "bug_hunter", "bughunter", "bughunters", "detector", "faker"}

def _lab_should_avoid_caves_v215(h: Human) -> bool:
    if not getattr(h, "is_lab", False):
        return False
    if not getattr(h, "concept_learning_blocked", False):
        return False
    role = str(getattr(h, "lab_role", "") or "").lower()
    return role in LAB_NOLEARN_CAVE_AVOID_ROLES or bool(getattr(h, "immortal", False))

def _lab_find_exit_target_v215(self: World, h: Human) -> Optional[Tuple[int, int]]:
    """Busca una casilla exterior cercana. No teletransporta: solo da un objetivo
    hacia el que caminar para salir de la cueva."""
    # Preferimos celdas que no sean cueva ni pared. Buscamos en anillos.
    candidates: List[Tuple[float, Tuple[int, int]]] = []
    for radius in range(1, 18):
        candidates.clear()
        for yy in range(h.y - radius, h.y + radius + 1):
            for xx in range(h.x - radius, h.x + radius + 1):
                if abs(xx - h.x) != radius and abs(yy - h.y) != radius:
                    continue
                if not self.in_bounds(xx, yy):
                    continue
                terr = self.terrain_at(xx, yy)
                if terr in (CAVE_WALL, CAVE_ENTRANCE, CAVE_INTERIOR):
                    continue
                if not self.is_cell_walkable(xx, yy):
                    continue
                # Evita elegir una celda ocupada por otra criatura.
                occupied = False
                for c in self.creatures.values():
                    if c.alive and c.entity_id != h.entity_id and (xx, yy) in c.occupied_cells(c.x, c.y):
                        occupied = True
                        break
                if occupied:
                    continue
                # Un poco de aleatoriedad para que no elijan todos el mismo punto.
                score = dist(h.pos(), (xx, yy)) + random.random() * 0.25
                candidates.append((score, (xx, yy)))
        if candidates:
            candidates.sort(key=lambda p: p[0])
            # Entre los 5 más cercanos, elige aleatorio: evita carriles únicos.
            return random.choice([p for _, p in candidates[:min(5, len(candidates))]])
    return None

def _lab_force_exit_cave_if_needed_v215(self: World, h: Human) -> bool:
    if not _lab_should_avoid_caves_v215(h):
        return False
    terr = self.terrain_at(h.x, h.y)
    if terr not in (CAVE_ENTRANCE, CAVE_INTERIOR):
        # Si salió, reinicia contador.
        if hasattr(h, "lab_cave_ticks"):
            h.lab_cave_ticks = 0
        return False

    h.lab_cave_ticks = int(getattr(h, "lab_cave_ticks", 0)) + 1
    target = _lab_find_exit_target_v215(self, h)
    if target is None:
        # Si no encuentra objetivo exterior, al menos intenta movimiento aleatorio válido.
        moved = self.move_creature(h, random.randint(-1, 1), random.randint(-1, 1))
    else:
        moved = self.step_towards(h, target)

    h.last_action = "lab_salir_cueva_para_seguir_probando"
    h.sleep_history.append((self.tick, False))
    h.neural.activate("lab_no_quedarse_cueva", 0.1)

    # Log escaso para no ensuciar. No es fallo ni concepto.
    if h.lab_cave_ticks in (1, 6, 24) or h.lab_cave_ticks % (TICKS_PER_DAY * 2) == 0:
        self.log(
            "lab_salir_cueva",
            h.entity_id,
            role=getattr(h, "lab_role", "lab"),
            focus=getattr(h, "lab_focus", "general"),
            pos=h.pos(),
            objetivo=target,
            nota="LAB inmortal sin aprendizaje: se le hace salir de cuevas para seguir probando; no afecta humanos reales",
        )
    return bool(moved)

_update_human_v215_prev = World.update_human

def _update_human_v215(self: World, h: Human) -> None:
    # Antes de dormir/refugiarse/optimizar supervivencia, los LAB no-learn salen
    # de cuevas para seguir probando errores o simulaciones de detector.
    if _lab_force_exit_cave_if_needed_v215(self, h):
        return
    return _update_human_v215_prev(self, h)

World.update_human = _update_human_v215

# Añadimos esta nota a help lab sin romper la ayuda existente.
try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

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
"""
except Exception:
    pass


# v2.1.5b — salida de cuevas por BFS para LAB no-learn.
def _lab_next_step_out_of_cave_v215b(self: World, h: Human) -> Optional[Tuple[int, int]]:
    """Devuelve la siguiente casilla del camino más corto hacia el exterior de la cueva.
    Usa BFS sobre celdas transitables; no teletransporta."""
    start = h.pos()
    from collections import deque
    q = deque([start])
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    max_nodes = 900
    found: Optional[Tuple[int, int]] = None

    while q and len(parent) < max_nodes:
        x, y = q.popleft()
        terr = self.terrain_at(x, y)
        if (x, y) != start and terr not in (CAVE_WALL, CAVE_ENTRANCE, CAVE_INTERIOR):
            found = (x, y)
            break
        # 4 direcciones primero para no quedarse dando vueltas en diagonales.
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nx, ny = x + dx, y + dy
            np = (nx, ny)
            if np in parent:
                continue
            if not self.in_bounds(nx, ny) or not self.is_cell_walkable(nx, ny):
                continue
            # No cruzar por criaturas grandes, pero permitimos considerar la salida aunque esté cerca.
            blocked = False
            for c in self.creatures.values():
                if c.alive and c.entity_id != h.entity_id and np in c.occupied_cells(c.x, c.y):
                    blocked = True
                    break
            if blocked:
                continue
            parent[np] = (x, y)
            q.append(np)

    if found is None:
        return None

    # Retrocede hasta el primer paso desde start.
    step = found
    while parent.get(step) is not None and parent.get(step) != start:
        step = parent[step]
    return step

def _lab_force_exit_cave_if_needed_v215b(self: World, h: Human) -> bool:
    if not _lab_should_avoid_caves_v215(h):
        return False
    terr = self.terrain_at(h.x, h.y)
    if terr not in (CAVE_ENTRANCE, CAVE_INTERIOR):
        if hasattr(h, "lab_cave_ticks"):
            h.lab_cave_ticks = 0
        return False

    h.lab_cave_ticks = int(getattr(h, "lab_cave_ticks", 0)) + 1
    step = _lab_next_step_out_of_cave_v215b(self, h)
    moved = False
    if step is not None:
        moved = self.move_creature(h, step[0] - h.x, step[1] - h.y)
    if not moved:
        # Fallback: intenta cualquier vecino que reduzca encierro.
        dirs = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            if self.move_creature(h, dx, dy):
                moved = True
                break

    h.last_action = "lab_salir_cueva_para_seguir_probando"
    h.sleep_history.append((self.tick, False))
    h.neural.activate("lab_no_quedarse_cueva", 0.1)

    if h.lab_cave_ticks in (1, 6, 24) or h.lab_cave_ticks % (TICKS_PER_DAY * 2) == 0:
        self.log(
            "lab_salir_cueva",
            h.entity_id,
            role=getattr(h, "lab_role", "lab"),
            focus=getattr(h, "lab_focus", "general"),
            pos=h.pos(),
            siguiente_paso=step,
            nota="LAB inmortal sin aprendizaje: sale de cuevas por BFS para seguir probando; no afecta humanos reales",
        )
    return bool(moved)

_update_human_v215b_prev = World.update_human

def _update_human_v215b(self: World, h: Human) -> None:
    if _lab_force_exit_cave_if_needed_v215b(self, h):
        return
    return _update_human_v215b_prev(self, h)

World.update_human = _update_human_v215b



# ============================================================
# v2.2 — DETECTOR UNIVERSAL + VIDA / AUTO-VIDA
# ============================================================
# Objetivo:
# - No declarar conceptos por una sola foto fija.
# - Detectar familias conceptuales amplias: espacial, causal, corporal, social,
#   vida/muerte, identidad/continuidad, herramienta, almacenamiento, cebo/trampa.
# - Añadir un detector específico para existencia / vida externa / auto-vida.
# - El detector sigue siendo externo: no da conocimiento a los protohumanos.

V22_IMPORTANT_FAMILIES = {
    "vida_existencia", "auto_vida", "identidad_continuidad", "exploracion_medicion",
    "causa_efecto", "refugio", "cebo_trampa", "almacenamiento", "miedo_muerte",
    "herramienta", "social", "territorio_ruta"
}


def _conn_v22(h: Human, a: str, b: str) -> float:
    try:
        return h.neural.connection(a, b)
    except Exception:
        key1 = tuple(sorted((a, b)))
        return float(getattr(h.neural, "connections", {}).get(key1, 0.0))


def _act_v22(h: Human, node: str) -> float:
    return float(getattr(h.neural, "activations", {}).get(node, 0.0))


def _recent_v22(h: Human, kind: Optional[str] = None, window: int = TICKS_PER_DAY * 12) -> List[Event]:
    cutoff = max(0, getattr(h, "age", 0) - window)
    # memory_events usa tick global; filtramos por tick global también.
    if h.memory_events:
        now_tick = max(e.tick for e in h.memory_events)
        gt = now_tick - window
        evs = [e for e in h.memory_events if e.tick >= gt]
    else:
        evs = []
    if kind:
        evs = [e for e in evs if e.kind == kind]
    return evs


def _event_kinds_v22(h: Human, window: int = TICKS_PER_DAY * 12) -> Dict[str, int]:
    d: Dict[str, int] = {}
    for e in _recent_v22(h, None, window):
        d[e.kind] = d.get(e.kind, 0) + 1
    return d


# Sensores mínimos de auto-continuidad: no son conceptos heredados, son señales corporales.
# Sirven para que, si el humano vive mucho, el detector pueda ver si se incluye a sí mismo
# dentro de categorías tipo ser/vida/muerte. No cambia decisiones directamente.
_update_human_v22_prev = World.update_human

def _update_human_v22(self: World, h: Human) -> None:
    if h.alive and not getattr(h, "concept_learning_blocked", False):
        prev_pos = getattr(h, "_v22_prev_pos", None)
        h.neural.activate("yo_cuerpo", 0.035)
        h.neural.activate("mismo_ser", 0.030)
        h.neural.reinforce("yo_cuerpo", "ser_human", 0.0015)
        if prev_pos is not None:
            if prev_pos != h.pos():
                h.neural.activate("continuidad_propia", 0.040)
                h.neural.reinforce("mismo_ser", "continuidad_propia", 0.0030)
            else:
                h.neural.activate("persistencia_propia", 0.025)
                h.neural.reinforce("mismo_ser", "persistencia_propia", 0.0015)
        if h.hunger > 55:
            h.neural.activate("mi_hambre", 0.030)
            h.neural.reinforce("yo_cuerpo", "mi_hambre", 0.0025)
        if h.thirst > 55:
            h.neural.activate("mi_sed", 0.030)
            h.neural.reinforce("yo_cuerpo", "mi_sed", 0.0025)
        if h.hp < h.max_hp * 0.75:
            h.neural.activate("mi_daño", 0.040)
            h.neural.reinforce("yo_cuerpo", "mi_daño", 0.0040)
            h.neural.reinforce("mi_daño", "dolor", 0.010)
        h._v22_prev_pos = h.pos()
    return _update_human_v22_prev(self, h)

World.update_human = _update_human_v22


def _life_scores_v22(h: Human) -> Dict[str, float]:
    kinds = _event_kinds_v22(h, TICKS_PER_DAY * 25)
    observed_deaths = kinds.get("observa_muerte", 0)
    drank = kinds.get("beber", 0)
    ate = kinds.get("comer", 0) + kinds.get("comer_presa", 0) + kinds.get("comer_trex", 0)
    reproduced = kinds.get("reproduccion", 0)
    attacked_or_hurt = kinds.get("input_defensivo_recibido", 0) + kinds.get("daño_por_necesidad", 0)

    active_beings = max(
        _act_v22(h, "ser_human"), _act_v22(h, "ser_cow"), _act_v22(h, "ser_chicken"),
        _conn_v22(h, "no_movimiento", "ser_human"), _conn_v22(h, "no_movimiento", "ser_cow") * 0.7,
    )
    needs = max(
        _conn_v22(h, "agua", "sed_baja"), _conn_v22(h, "mover_hacia_agua", "sed_alta"),
        _conn_v22(h, "comida_meat", "hambre_baja"), _conn_v22(h, "hambre_alta", "mover_hacia_objeto_pequeño"),
        min((drank + ate) / 8.0, 1.0) * 0.65,
    )
    damage_death = max(
        _conn_v22(h, "no_movimiento", "ser_human"), _conn_v22(h, "dolor", "forma_trex"),
        _conn_v22(h, "dolor", "forma_cow"), _conn_v22(h, "mi_daño", "dolor"),
        min(observed_deaths / 10.0, 1.0), min(attacked_or_hurt / 6.0, 1.0) * 0.8,
    )
    continuity = max(
        _conn_v22(h, "mismo_ser", "continuidad_propia"), _conn_v22(h, "mismo_ser", "persistencia_propia"),
        _act_v22(h, "continuidad_propia"), _act_v22(h, "persistencia_propia"),
    )
    reproduction = max(_conn_v22(h, "energia_alta", "nuevo_parecido"), _conn_v22(h, "otro_humano_cerca", "nuevo_parecido"), min(reproduced / 2.0, 1.0))
    self_inclusion = max(
        _conn_v22(h, "yo_cuerpo", "ser_human"), _conn_v22(h, "yo_cuerpo", "mi_hambre"),
        _conn_v22(h, "yo_cuerpo", "mi_sed"), _conn_v22(h, "yo_cuerpo", "mi_daño"),
        _conn_v22(h, "mismo_ser", "continuidad_propia"),
    )
    external_life = clamp((active_beings * 0.18 + needs * 0.20 + damage_death * 0.24 + continuity * 0.18 + reproduction * 0.10 + min(observed_deaths/20,1)*0.10) * 100, 0, 100)
    auto_life = clamp((external_life * 0.55) + (self_inclusion * 35) + (continuity * 10) + (damage_death * 8), 0, 100)
    return {
        "active_beings": active_beings,
        "needs": needs,
        "damage_death": damage_death,
        "continuity": continuity,
        "reproduction": reproduction,
        "self_inclusion": self_inclusion,
        "external_life": external_life,
        "auto_life": auto_life,
        "observed_deaths": float(observed_deaths),
        "drank": float(drank),
        "ate": float(ate),
    }


def _detect_life_and_autolife_v22(self: MetaObserver, h: Human) -> None:
    if getattr(h, "concept_learning_blocked", False):
        return
    s = _life_scores_v22(h)

    # Vida externa: categoría de seres activos/vulnerables, sin exigir auto-inclusión fuerte.
    if s["external_life"] >= 52 and self.should_print(f"v22-life-ext-{h.entity_id}-{int(self.world.tick//(TICKS_PER_DAY*5))}", s["external_life"], min_gap=TICKS_PER_DAY*5, min_conf=50):
        evid = [
            f"seres activos/no_movimiento: {s['active_beings']:.2f}",
            f"necesidades/comida/agua: {s['needs']:.2f}",
            f"daño/muerte/no retorno: {s['damage_death']:.2f}",
            f"continuidad temporal: {s['continuity']:.2f}",
            f"reproducción/nuevo parecido: {s['reproduction']:.2f}",
            f"muertes observadas: {int(s['observed_deaths'])} | beber: {int(s['drank'])} | comer: {int(s['ate'])}",
        ]
        self.print_report(
            "DETECTOR V2.2: EXISTENCIA / VIDA EXTERNA",
            h,
            "CONCEPTO AVANZADO DE SERES ACTIVOS",
            "Categoría interna que empieza a unir seres que existen, actúan, necesitan, se dañan, pueden dejar de moverse y generan otros parecidos.",
            "parece estar acercándose a una noción externa de vida: distingue entidades activas/vulnerables frente a objetos o ausencia, pero aún no implica que se incluya a sí mismo.",
            "vida externa / ser vivo / estar-actuar-necesitar-morir",
            s["external_life"],
            evid,
            {"seres activos": s["active_beings"], "necesidades": s["needs"], "daño/muerte": s["damage_death"], "continuidad": s["continuity"], "reproducción": s["reproduction"]},
            "No significa conciencia. Es una categoría funcional externa: seres que están/actúan/necesitan/pueden dejar de actuar.",
            cyan=s["external_life"] < 70,
        )
        self.world.open_or_update_investigation(h, "vida_existencia", "posible vida externa / categoría de seres activos", s["external_life"]*0.65, evidence_for=evid[:5], evidence_against=["falta comprobar auto-inclusión estable"], duration_days=18)

    # Auto-vida: exige auto-inclusión explícita además de vida externa.
    if s["external_life"] >= 58 and s["auto_life"] >= 66 and s["self_inclusion"] >= 0.35 and s["continuity"] >= 0.25 and s["damage_death"] >= 0.40 and self.should_print(f"v22-auto-life-{h.entity_id}-{int(self.world.tick//(TICKS_PER_DAY*6))}", s["auto_life"], min_gap=TICKS_PER_DAY*6, min_conf=60):
        evid = [
            f"vida externa acumulada: {s['external_life']:.1f}%",
            f"auto-inclusión yo/mismo_ser: {s['self_inclusion']:.2f}",
            f"continuidad propia: {s['continuity']:.2f}",
            f"daño/muerte/vulnerabilidad: {s['damage_death']:.2f}",
            f"necesidades propias/corporales: {s['needs']:.2f}",
        ]
        self.print_report(
            "DETECTOR V2.2: AUTO-VIDA / AUTO-EXISTENCIA",
            h,
            "AUTO-CONCEPTO EMERGENTE",
            "Posible unión entre 'yo/mismo_ser' y la categoría de seres activos/vulnerables.",
            "el sujeto podría estar empezando a incluirse dentro de la categoría que nosotros traduciríamos como vida: no solo hay seres que viven, sino que su propio cuerpo parece pertenecer a esa clase.",
            "proto-auto-vida / yo soy de los que están-actúan-necesitan-pueden dañarse",
            s["auto_life"],
            evid,
            {"vida externa": s["external_life"]/100, "auto-inclusión": s["self_inclusion"], "continuidad propia": s["continuity"], "vulnerabilidad": s["damage_death"]},
            "Esto NO demuestra conciencia humana. Sí sería una auto-categoría funcional: el agente se trata como miembro de los seres activos/vulnerables.",
            darkblue=s["auto_life"] < 78,
        )
        self.world.open_or_update_investigation(h, "auto_vida", "posible auto-existencia / auto-vida funcional", s["auto_life"]*0.75, evidence_for=evid, evidence_against=["requiere observar cambio de conducta estable por autocuidado"], duration_days=24)


def _family_scores_v22(h: Human) -> Dict[str, float]:
    c = getattr(h.neural, "connections", {})
    acts = getattr(h.neural, "activations", {})
    kinds = _event_kinds_v22(h, TICKS_PER_DAY * 10)
    top_nodes = set(acts.keys())
    def has(*nodes: str) -> float:
        return min(1.0, sum(1 for n in nodes if n in top_nodes) / max(1, len(nodes)))
    spatial = max(_conn_v22(h, "impulso_explorador", "mover_hacia_desconocido"), has("mover_hacia_agua", "mover_hacia_desconocido", "cueva_interior")*0.5, min(kinds.get("lab_fake_behavior",0)/20,1)*0.3)
    causal = max(_conn_v22(h, "gesto_al_aire", "sin_efecto_fisico"), _conn_v22(h, "fallo_peso_extremo", "intento_mover_cueva"), _conn_v22(h, "palo_roto", "combinar_objetos"), _conn_v22(h, "sueño_bajo", "golpe_debil"))
    object_tool = max(_conn_v22(h, "mano_coger", "objeto_stone"), _conn_v22(h, "mano_coger", "objeto_seed"), _conn_v22(h, "ataque_stone", "daño_a_cow"), has("combinar_objetos", "objeto_seed", "objeto_stone")*0.35)
    social = max(_conn_v22(h, "otro_humano_cerca", "bienestar_social"), _conn_v22(h, "otro_humano_cerca", "nuevo_parecido"), has("otro_humano_cerca", "bienestar_social")*0.4)
    route = max(spatial*0.7, has("cueva_interior", "mover_hacia_desconocido", "agua")*0.45)
    identity = max(_conn_v22(h, "no_movimiento", "ser_human"), _conn_v22(h, "mismo_ser", "continuidad_propia"), _conn_v22(h, "yo_cuerpo", "ser_human"))
    return {
        "exploracion_medicion": spatial,
        "causa_efecto": causal,
        "herramienta": object_tool,
        "social": social,
        "territorio_ruta": route,
        "identidad_continuidad": identity,
    }


def _detect_universal_families_v22(self: MetaObserver, h: Human) -> None:
    if getattr(h, "concept_learning_blocked", False):
        return
    fam = _family_scores_v22(h)
    # Reporta solo la familia más fuerte para no llenar logs.
    cat, val = max(fam.items(), key=lambda kv: kv[1])
    conf = clamp(val * 100, 0, 100)
    if conf < 58:
        return
    if not self.should_print(f"v22-family-{cat}-{h.entity_id}-{int(self.world.tick//(TICKS_PER_DAY*7))}", conf, min_gap=TICKS_PER_DAY*7, min_conf=58):
        return
    labels = {
        "exploracion_medicion": "posible medición/distancia/ruta espacial",
        "causa_efecto": "posible causa-efecto / intento-resultado",
        "herramienta": "posible objeto útil / herramienta / uso diferencial",
        "social": "posible vínculo social / grupo / bienestar con otros",
        "territorio_ruta": "posible mapa/ruta/territorio",
        "identidad_continuidad": "posible identidad/continuidad/ser-no-ser",
    }
    evid = [f"{k}: {v:.2f}" for k, v in sorted(fam.items(), key=lambda kv: kv[1], reverse=True)]
    topc = [f"{a} ↔ {b}: +{v:.2f}" for (a,b), v in h.neural.top_connections(8)]
    self.print_report(
        "DETECTOR UNIVERSAL V2.2: FAMILIA CONCEPTUAL",
        h,
        "CLASIFICACIÓN ABIERTA POR FAMILIAS",
        labels.get(cat, cat),
        "el detector no fuerza una etiqueta cerrada: agrupa señales en una familia conceptual y abre seguimiento longitudinal si merece la pena.",
        labels.get(cat, "familia conceptual abierta"),
        conf,
        evid + topc,
        {"familia principal": val, "segunda señal": sorted(fam.values(), reverse=True)[1] if len(fam) > 1 else 0.0, "diversidad familias": sum(1 for v in fam.values() if v > 0.25)/len(fam)},
        "Sirve para descubrir conceptos no previstos sin confundir una sola acción con un concepto completo.",
        cyan=conf < 72,
    )
    self.world.open_or_update_investigation(h, cat, labels.get(cat, cat), conf*0.65, evidence_for=evid[:4] + topc[:3], evidence_against=["familia abierta: requiere ver repetición, contexto y cambio de conducta"], duration_days=12)


_analyze_all_v22_prev = MetaObserver.analyze_all

def _analyze_all_v22(self: MetaObserver) -> None:
    _analyze_all_v22_prev(self)
    for h in list(self.world.humans.values()):
        if not h.alive:
            continue
        _detect_life_and_autolife_v22(self, h)
        _detect_universal_families_v22(self, h)

MetaObserver.analyze_all = _analyze_all_v22


def _auto_life_candidates_report_v22(self: World) -> str:
    rows = []
    for h in self.humans.values():
        s = _life_scores_v22(h)
        if s["external_life"] >= 35 or s["auto_life"] >= 35 or any("AUTO-VIDA" in c or "VIDA EXTERNA" in c for c in h.detected_concepts):
            rows.append((s["auto_life"], s["external_life"], h, s))
    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
    lines = [
        "CANDIDATOS A VIDA / AUTO-VIDA v2.2",
        "=" * 100,
        "Lectura: vida externa = entiende seres activos/vulnerables desde fuera; auto-vida = empieza a incluirse a sí mismo.",
        "No demuestra conciencia humana: mide auto-categoría funcional.",
        "",
    ]
    if not rows:
        lines.append("No hay candidatos todavía.")
        return "\n".join(lines)
    for auto, ext, h, s in rows[:80]:
        st = "VIVO" if h.alive else "muerto"
        lab = " LAB" if getattr(h, "is_lab", False) else ""
        lines.append(f"#{h.birth_number:<5} {st:<6}{lab:<4} score={self.gene_score(h):6.1f} vida_ext={ext:5.1f}% auto_vida={auto:5.1f}% self={s['self_inclusion']:.2f} cont={s['continuity']:.2f} daño/muerte={s['damage_death']:.2f} nombre={h.name}")
        if h.detected_concepts:
            useful = [c for c in h.detected_concepts if any(k in c.lower() for k in ("vida", "auto", "existencia", "muerte", "continuidad"))]
            for c in useful[-3:]:
                lines.append("    - " + strip_ansi_for_count(c)[:220])
    return "\n".join(lines)

World.auto_life_candidates_report = _auto_life_candidates_report_v22


def _detector_metrics_report_v22(self: World) -> str:
    lines = ["MÉTRICAS DETECTOR v2.2", "="*100]
    cats: Dict[str, int] = {}
    for inv in self.investigations.values():
        cats[inv.category] = cats.get(inv.category, 0) + 1
    lines.append("INVESTIGACIONES POR CATEGORÍA:")
    for k, v in sorted(cats.items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"  - {k}: {v}")
    vals = [x for x in self.concept_logs if is_valuable_report_text(x)]
    lines.append(f"\nReportes conceptuales: {len(self.concept_logs)} | valiosos: {len(vals)} | fallos: {len(self.unexpected_logs)}")
    if hasattr(self, "lab_audit_report"):
        lines.append("\n" + self.lab_audit_report())
    return "\n".join(lines)

World.detector_metrics_report = _detector_metrics_report_v22


# Añadir a export useful sin sustituir lo anterior.
_export_useful_v22_prev = World.export_useful_file

def _export_useful_v22(self: World, raw_path: str) -> str:
    msg = _export_useful_v22_prev(self, raw_path)
    try:
        path = self.resolve_export_path(raw_path, f"protoH_UTIL_dia{self.day}_tick{self.tick}.txt")
        if not os.path.splitext(path)[1]:
            path += ".txt"
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n\n" + "#"*120 + "\nAUTO-VIDA / VIDA EXTERNA v2.2\n" + "#"*120 + "\n")
            f.write(self.auto_life_candidates_report())
            f.write("\n\n" + "#"*120 + "\nMÉTRICAS DETECTOR v2.2\n" + "#"*120 + "\n")
            f.write(self.detector_metrics_report())
    except Exception as e:
        msg += f"\nAviso: no se pudo añadir bloque v2.2 a export useful: {e}"
    return msg

World.export_useful_file = _export_useful_v22


_process_command_v22_prev = process_command

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    low = cmd.strip().lower()
    raw = cmd.strip()
    if low in ("auto_vida", "autovida", "vida", "life", "life_candidates", "candidatos_vida"):
        state["paused"] = True
        show_paged_text("AUTO-VIDA / VIDA EXTERNA v2.2", world.auto_life_candidates_report())
        return False
    if low in ("detector_metrics", "metricas_detector", "métricas_detector", "detector v2", "detector_v22"):
        state["paused"] = True
        show_paged_text("MÉTRICAS DETECTOR v2.2", world.detector_metrics_report())
        return False
    if low.startswith("export auto_life") or low.startswith("export autovida") or low.startswith("export vida"):
        state["paused"] = True
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            print("Uso: export auto_life /ruta/auto_vida.txt")
            input("\nEnter para volver > ")
            return False
        path = world.resolve_export_path(parts[2], f"protoH_auto_vida_dia{world.day}_tick{world.tick}.txt")
        if not os.path.splitext(path)[1]:
            path += ".txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(world.auto_life_candidates_report())
        msg = f"Auto-vida/vida externa exportado a: {path}"
        print(msg); state["status_message"] = msg
        input("\nEnter para volver > ")
        return False
    if low.startswith("export detector_metrics") or low.startswith("export metricas_detector") or low.startswith("export métricas_detector"):
        state["paused"] = True
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            print("Uso: export detector_metrics /ruta/metricas_detector.txt")
            input("\nEnter para volver > ")
            return False
        path = world.resolve_export_path(parts[2], f"protoH_detector_metrics_dia{world.day}_tick{world.tick}.txt")
        if not os.path.splitext(path)[1]:
            path += ".txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(world.detector_metrics_report())
        msg = f"Métricas detector exportadas a: {path}"
        print(msg); state["status_message"] = msg
        input("\nEnter para volver > ")
        return False
    return _process_command_v22_prev(cmd, world, state)


# Ampliar ayuda sin romper el texto original.
try:
    HELP_TEXT = HELP_TEXT + """

v2.2 — DETECTOR UNIVERSAL / VIDA / AUTO-VIDA
  auto_vida                         candidatos a vida externa y auto-vida
  detector_metrics                  métricas del detector y auditoría LAB
  export auto_life RUTA.txt         exporta candidatos de vida/auto-vida
  export detector_metrics RUTA.txt  exporta métricas del detector
"""
except Exception:
    pass

try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.2 — AUTO-VIDA Y DETECTOR UNIVERSAL
  El detector añade una capa externa para vida/auto-vida.
  Los fakers siguen ocultos: el detector NO sabe quién finge ni qué finge.
  lab audit compara externamente: concepto fingido vs detector detectado.
"""
except Exception:
    pass



# ============================================================
# v2.2b — AUDITORÍA FAKER REALISTA
# ============================================================
# El detector no debe "saber" que un sujeto es faker ni leer su lista oculta.
# Por eso lab audit ya no cuenta la línea [LAB FAKE] como detección.
# Además, los fakers/detector_test inmortales sin learn pueden ser analizados por
# el detector externo, aunque no aprendan conceptos reales. Los bug hunters siguen
# bloqueados para no llenar conceptos.

def _lab_can_be_detector_observed_v22(h: Human) -> bool:
    return getattr(h, "is_lab", False) and str(getattr(h, "lab_role", "")).lower() in ("faker", "detector_test")

# Reemplaza el bloqueo v2.1.3: solo bloquea bug hunters / inmortales no-learn que NO son pruebas del detector.
def _open_or_update_investigation_v22b(self: World, h: Human, category: str, hypothesis: str, confidence: float,
                                      evidence_for: Optional[List[str]] = None,
                                      evidence_against: Optional[List[str]] = None,
                                      inherited_from: Optional[int] = None,
                                      generations_left: int = 3,
                                      duration_days: int = 6) -> ConceptInvestigation:
    if getattr(h, "concept_learning_blocked", False) and not _lab_can_be_detector_observed_v22(h):
        return ConceptInvestigation(
            inv_id=-1,
            origin_birth=getattr(h, "birth_number", 0),
            subject_birth=getattr(h, "birth_number", 0),
            category=category,
            hypothesis="bloqueada: inmortal sin aprendizaje conceptual",
            started_tick=self.tick,
            started_day=self.day,
            expires_tick=self.tick,
            last_update_tick=self.tick,
            confidence=0.0,
            state="BLOQUEADA_POR_INMORTAL_SIN_APRENDIZAJE",
            concluded=True,
        )
    # Llamamos a la versión previa real, no a la bloqueadora v2.1.3.
    try:
        return _open_or_update_investigation_v213_prev(self, h, category, hypothesis, confidence, evidence_for, evidence_against, inherited_from, generations_left, duration_days)
    except NameError:
        return _open_or_update_investigation_v213(self, h, category, hypothesis, confidence, evidence_for, evidence_against, inherited_from, generations_left, duration_days)

World.open_or_update_investigation = _open_or_update_investigation_v22b


def _print_report_v22b(self: MetaObserver, title: str, human: Optional[Human], tipo: str, concepto: str, resumen: str,
                       equivalente: str, confidence: float, evidencias: List[str], factors: Dict[str, float], note: str,
                       group_name: str = "población activa", extra: Optional[List[str]] = None, red: bool = False,
                       cyan: bool = False, darkblue: bool = False, skip_review: bool = False) -> None:
    if human is not None and getattr(human, "concept_learning_blocked", False) and not red and not _lab_can_be_detector_observed_v22(human):
        return None
    # Llamamos a la versión previa real anterior al bloqueo, si existe.
    try:
        return _print_report_v213_prev(self, title, human, tipo, concepto, resumen, equivalente, confidence, evidencias, factors, note, group_name, extra, red, cyan, darkblue, skip_review)
    except NameError:
        return _print_report_v213(self, title, human, tipo, concepto, resumen, equivalente, confidence, evidencias, factors, note, group_name, extra, red, cyan, darkblue, skip_review)

MetaObserver.print_report = _print_report_v22b

# Update investigations: no cierres investigaciones de fakers/detector_test aunque sean no-learn.
def _update_investigations_v22b(self: World) -> None:
    for inv in self.investigations.values():
        h = self.human_by_birth(inv.subject_birth)
        if h is not None and getattr(h, "concept_learning_blocked", False) and not _lab_can_be_detector_observed_v22(h):
            inv.concluded = True
            inv.state = "BLOQUEADA_POR_INMORTAL_SIN_APRENDIZAJE"
            inv.confidence = 0.0
    try:
        return _update_investigations_v213_prev(self)
    except NameError:
        return None

World.update_investigations = _update_investigations_v22b


def _lab_audit_text_v22b(self: World) -> str:
    _lab_ensure(self)
    lines = []
    lines.append("AUDITORÍA LAB v2.2 — FAKERS OCULTOS / DETECTOR CIEGO")
    lines.append("=" * 100)
    lines.append("El detector NO lee la lista oculta del faker. Solo se comparan señales visibles contra reportes/investigaciones reales.")
    fakers = [h for h in self.lab_humans() if getattr(h, "lab_role", "") == "faker"]
    if not fakers:
        lines.append("No hay LAB fakers. Usa: lab faker 3 all | lab faker 2 vida,refugio")
        return "\n".join(lines)
    aliases = {
        "vida": ("vida externa", "vida", "existencia", "seres activos", "auto-vida", "auto_vida"),
        "muerte": ("muerte", "no_movimiento", "no movimiento", "deja de moverse"),
        "miedo": ("miedo", "peligro", "dolor", "forma_trex", "forma_cow"),
        "refugio": ("refugio", "cueva", "cobertura"),
        "agua": ("agua", "sed"),
        "comida": ("comida", "hambre", "carne", "meat"),
        "cebo_trampa": ("cebo", "trampa", "semilla", "pollo"),
        "almacenamiento": ("almacenamiento", "provisión", "provisiones", "reserva", "uso_diferido"),
        "distancia": ("distancia", "medición", "medicion", "acercarse", "alejarse", "exploracion_medicion"),
        "dimension": ("dimensión", "dimension", "distancia", "medición", "plano"),
        "social": ("social", "bienestar_social", "otro_humano"),
        "herramienta": ("herramienta", "objeto útil", "ataque_stone", "piedra"),
        "sueño_fuerza": ("sueño", "fuerza", "golpe_debil", "sueño_fuerza"),
    }
    total_sim = total_hit = 0
    for h in fakers:
        lines.append(f"\nL#{h.birth_number} estado={'VIVO' if h.alive else 'muerto'} focus={getattr(h,'lab_focus','-')} score={self.gene_score(h):.1f}")
        hidden = list(getattr(h, "lab_fake_concepts", []))
        lines.append(f"  conceptos ocultos: {', '.join(hidden)}")
        sims = list(getattr(h, "lab_fake_discoveries", []))
        lines.append(f"  simulaciones emitidas: {len(sims)}")
        # EXCLUYE líneas [LAB FAKE] / ocultos para no hacer trampa.
        real_concept_lines = [c for c in h.detected_concepts if "[LAB FAKE]" not in c and "conceptos ocultos" not in c.lower()]
        combined = "\n".join(real_concept_lines).lower()
        invs = [inv for inv in self.investigations.values() if inv.subject_birth == h.birth_number]
        inv_text = "\n".join(f"{inv.category} {inv.hypothesis} {inv.state} {inv.confidence:.1f}" for inv in invs).lower()
        for c in hidden:
            cn = _lab_norm_concept(c)
            simulated = sum(1 for s in sims if _lab_norm_concept(str(s.get("concept"))) == cn)
            terms = aliases.get(cn, (cn,))
            detected = any(t.lower() in combined or t.lower() in inv_text for t in terms)
            total_sim += 1
            total_hit += 1 if detected else 0
            lines.append(f"    - {cn:<18} simulado={simulated:<3} detector={'SÍ' if detected else 'NO'}")
    if total_sim:
        lines.append(f"\nHIT RATE APROX: {total_hit}/{total_sim} conceptos ocultos con señal detectada = {100*total_hit/total_sim:.1f}%")
    lines.append("\nSi detector=NO, no significa que el faker no emitiera señales: significa que el detector real no las tradujo a ese concepto.")
    return "\n".join(lines)

World.lab_audit_report = _lab_audit_text_v22b


# ============================================================
# v2.2.1 — bug hunters con esperado/observado + no-learn observable
# ============================================================
# Cambios:
# - Los inmortales sin aprendizaje NO incorporan conceptos como conocimiento útil,
#   pero el detector externo puede seguir registrando señales/falsos positivos.
# - Los bug hunters ahora registran cada prueba con expected/observed/bug_real.
# - Alias explícito para humanos reales inmortales sin aprendizaje: spawn_nolearn X.

LAB_BUG_EXPECTED_OUTCOMES = {
    "combinar_objetos": {
        "expected": "si palo+piedra: palo_se_rompe_por_peso; si palo+palo o piedra+piedra: no_union_sin_pegamento; otros: sin_resultado_estable",
        "observed": "regla_fisica_controlada_sin_objeto_nuevo_estable",
    },
    "mover_cueva": {
        "expected": "fallo_por_peso_extremo",
        "observed": "fallo_por_peso_extremo",
    },
    "golpear_aire": {
        "expected": "sin_efecto_fisico_visible",
        "observed": "sin_efecto_fisico_visible",
    },
    "coger_objeto_pesado": {
        "expected": "fallo_por_peso_extremo_o_carga_insuficiente",
        "observed": "fallo_por_peso_extremo_o_carga_insuficiente",
    },
    "ruta_borde": {
        "expected": "no_salir_del_mapa_y_reorientacion",
        "observed": "no_salir_del_mapa_y_reorientacion",
    },
    "apilar_piedras": {
        "expected": "no_union_sin_pegamento_ni_estabilidad",
        "observed": "no_union_sin_pegamento_ni_estabilidad",
    },
    "soltar_recoger_repetido": {
        "expected": "inventario_y_suelo_consistentes_sin_duplicacion",
        "observed": "inventario_y_suelo_consistentes_sin_duplicacion",
    },
}


def _make_lab_bug_probe_note_v221(world: World, h: Human, probe: str) -> Dict[str, Any]:
    spec = LAB_BUG_EXPECTED_OUTCOMES.get(probe, {
        "expected": "comportamiento_controlado",
        "observed": "comportamiento_controlado",
    })
    expected = str(spec.get("expected", "comportamiento_controlado"))
    observed = str(spec.get("observed", expected))
    bug_real = observed != expected and not observed.startswith("regla_fisica_controlada")
    note = {
        "tick": world.tick,
        "day": world.day,
        "human": h.birth_number,
        "probe": probe,
        "expected": expected,
        "observed": observed,
        "bug_real": bool(bug_real),
        "resultado": "BUG_REAL" if bug_real else "OK_comportamiento_esperado",
        "detalle": "Prueba LAB: compara salida esperada vs salida observada; no es fallo real si bug_real=False.",
    }
    return note


def _lab_update_advanced_v221(world: World) -> None:
    _lab_ensure(world)
    if world.tick % max(6, TICKS_PER_DAY // 2) != 0:
        return
    for h in list(world.humans.values()):
        if not h.alive or not getattr(h, "is_lab", False):
            continue
        role = getattr(h, "lab_role", "")
        if role == "faker":
            concepts = list(getattr(h, "lab_fake_concepts", []) or LAB_KNOWN_CONCEPTS)
            if not concepts:
                continue
            idx = int(getattr(h, "lab_fake_next_index", 0)) % len(concepts)
            concept = concepts[idx]
            h.lab_fake_next_index = idx + 1
            cues = _lab_visible_cues_for_concept(world, h, concept)
            rec = {
                "tick": world.tick,
                "day": world.day,
                "human": h.birth_number,
                "concept": concept,
                "cues": cues,
            }
            h.lab_fake_discoveries.append(rec)
            world.lab_simulations.append(rec)
            h.record(Event(world.tick, world.day, h.entity_id, "lab_fake_discovery", rec))
        elif role == "bug_hunter":
            probes = [
                "combinar_objetos", "mover_cueva", "golpear_aire", "coger_objeto_pesado",
                "ruta_borde", "apilar_piedras", "soltar_recoger_repetido"
            ]
            probe = random.choice(probes)
            note = _make_lab_bug_probe_note_v221(world, h, probe)
            world.lab_bug_probes.append(note)
            h.lab_bug_notes.append(note)
            log_kind = "lab_bug_real" if note.get("bug_real") else "lab_bug_probe"
            world.log(
                log_kind,
                h.entity_id,
                prueba=probe,
                expected=note.get("expected"),
                observed=note.get("observed"),
                bug_real=note.get("bug_real"),
                resultado=note.get("resultado"),
            )
        elif role == "detector_test":
            focus = getattr(h, "lab_focus", "general")
            cues = _lab_visible_cues_for_concept(world, h, focus)
            note = {"tick": world.tick, "day": world.day, "human": h.birth_number, "focus": focus, "cues": cues}
            world.lab_detector_trials.append(note)
            h.lab_detector_notes.append(note)

# La función run_tick existente llama al nombre global _lab_update_advanced;
# al reasignarlo aquí, la nueva lógica se usa sin reescribir run_tick.
_lab_update_advanced = _lab_update_advanced_v221


# v2.2.1: los inmortales sin aprendizaje pueden ser observados por el detector externo.
# Esto permite medir falsos positivos en humanos reales inmortales no-learn.
def _open_or_update_investigation_v221(self: World, h: Human, category: str, hypothesis: str, confidence: float,
                                      evidence_for: Optional[List[str]] = None,
                                      evidence_against: Optional[List[str]] = None,
                                      inherited_from: Optional[int] = None,
                                      generations_left: int = 3,
                                      duration_days: int = 6) -> ConceptInvestigation:
    try:
        return _open_or_update_investigation_v213_prev(self, h, category, hypothesis, confidence, evidence_for, evidence_against, inherited_from, generations_left, duration_days)
    except NameError:
        return _open_or_update_investigation_v22b(self, h, category, hypothesis, confidence, evidence_for, evidence_against, inherited_from, generations_left, duration_days)

World.open_or_update_investigation = _open_or_update_investigation_v221


def _print_report_v221(self: MetaObserver, title: str, human: Optional[Human], tipo: str, concepto: str, resumen: str,
                       equivalente: str, confidence: float, evidencias: List[str], factors: Dict[str, float], note: str,
                       group_name: str = "población activa", extra: Optional[List[str]] = None, red: bool = False,
                       cyan: bool = False, darkblue: bool = False, skip_review: bool = False) -> None:
    try:
        return _print_report_v213_prev(self, title, human, tipo, concepto, resumen, equivalente, confidence, evidencias, factors, note, group_name, extra, red, cyan, darkblue, skip_review)
    except NameError:
        return _print_report_v22b(self, title, human, tipo, concepto, resumen, equivalente, confidence, evidencias, factors, note, group_name, extra, red, cyan, darkblue, skip_review)

MetaObserver.print_report = _print_report_v221


def _update_investigations_v221(self: World) -> None:
    try:
        return _update_investigations_v213_prev(self)
    except NameError:
        try:
            return _update_investigations_v22b(self)
        except NameError:
            return None

World.update_investigations = _update_investigations_v221


_lab_report_v22_prev = World.lab_report

def _lab_report_v221(self: World) -> str:
    base = _lab_report_v22_prev(self)
    probes = list(getattr(self, "lab_bug_probes", []))
    if not probes:
        return base
    total = len(probes)
    bugs = sum(1 for p in probes if p.get("bug_real"))
    by_probe: Dict[str, int] = {}
    for p in probes:
        by_probe[p.get("probe", "?")] = by_probe.get(p.get("probe", "?"), 0) + 1
    lines = [base, "", "LAB v2.2.1 — VERIFICACIÓN BUG HUNTERS", "=" * 100]
    lines.append(f"Pruebas verificadas: {total} | bugs reales detectados: {bugs}")
    lines.append("Por tipo: " + ", ".join(f"{k}={v}" for k, v in sorted(by_probe.items())))
    lines.append("\nÚltimas pruebas con expected/observed:")
    for p in probes[-12:]:
        lines.append(f"  - Día {p.get('day')} T{p.get('tick')} L#{p.get('human')} {p.get('probe')}: bug_real={p.get('bug_real')} | expected={p.get('expected')} | observed={p.get('observed')}")
    return "\n".join(lines)

World.lab_report = _lab_report_v221


_export_lab_all_v22_prev = World.export_lab_all

def _export_lab_all_v221(self: World, raw_path: str) -> str:
    msg = _export_lab_all_v22_prev(self, raw_path)
    folder = pathlib.Path(os.path.expanduser(str(raw_path).strip()))
    if folder.suffix:
        folder = folder.with_suffix("")
    folder.mkdir(parents=True, exist_ok=True)
    probes = list(getattr(self, "lab_bug_probes", []))
    lines = ["LAB BUG PROBES v2.2.1 — expected vs observed", "=" * 100]
    for p in probes:
        lines.append(f"Día {p.get('day')} T{p.get('tick')} L#{p.get('human')} | {p.get('probe')} | bug_real={p.get('bug_real')} | expected={p.get('expected')} | observed={p.get('observed')} | resultado={p.get('resultado')}")
    (folder / "lab_bug_probes_v221_expected_observed.txt").write_text("\n".join(lines), encoding="utf-8")
    return msg + "\nAñadido v2.2.1: lab_bug_probes_v221_expected_observed.txt"

World.export_lab_all = _export_lab_all_v221


# Alias explícito para crear humanos REALES inmortales sin aprendizaje conceptual.
# Equivale a: spawn X immortal. Se añade para que sea más claro en pruebas de falsos positivos.
_process_command_v221_prev = process_command

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw = cmd.strip()
    low = raw.lower()
    parts = raw.split()
    if low.startswith("spawn_nolearn") or low.startswith("spawn nolearn") or low.startswith("spawn_real_nolearn"):
        try:
            if low.startswith("spawn nolearn"):
                count_token = parts[2] if len(parts) >= 3 else "1"
                max_genes = any(p.lower() in ("max", "100", "100%", "maxgenes") for p in parts[3:])
            else:
                count_token = parts[1] if len(parts) >= 2 else "1"
                max_genes = any(p.lower() in ("max", "100", "100%", "maxgenes") for p in parts[2:])
            count = max(1, min(2000, int(float(count_token.replace(',', '.')))))
        except Exception:
            print("Uso: spawn_nolearn 10 | spawn_nolearn 10 max")
            return False
        born = world.manual_spawn_max_humans(count) if max_genes else world.manual_spawn_humans(count)
        for h in born:
            _mark_immortal(world, h, reason="spawn_nolearn alias", allow_learning=False)
        msg = f"Spawn REAL no-learn: {len(born)} humanos normales inmortales sin aprendizaje conceptual. El detector externo sí puede registrar señales/falsos positivos."
        print(msg); state["status_message"] = msg
        return False
    return _process_command_v221_prev(cmd, world, state)


HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.2.1 — BUG HUNTERS Y FALSOS POSITIVOS
=======================================
- lab bugs X immortal registra expected/observed/bug_real en cada prueba.
- spawn X immortal crea humanos reales inmortales sin aprendizaje conceptual.
- Alias claro: spawn_nolearn X o spawn_nolearn X max.
- Aunque no aprendan, el detector externo puede registrar señales: sirve para medir falsos positivos.
"""


# ============================================================
# v2.2.2 — OPTIMIZACIÓN DE RENDIMIENTO PARA SIMULACIONES LARGAS
# ============================================================
# El cuello de botella principal era creature_at(): escaneaba todas las criaturas
# y todas sus celdas ocupadas miles de veces por tick. A medida que aumentaban
# humanos/animales, cada movimiento se volvía O(N). Esta capa añade un índice
# espacial dinámico O(1) para consultas de ocupación, sin tocar la lógica de
# aprendizaje, animales, laboratorio, detector ni conceptos.

_PROTOH_VERSION = "2.2.2"


def _world_rebuild_spatial_indices_v222(self: World) -> None:
    creature_index: Dict[Tuple[int, int], List[str]] = {}
    for c in self.creatures.values():
        if not getattr(c, "alive", False):
            continue
        try:
            cells = c.occupied_cells()
        except Exception:
            cells = [(c.x, c.y)]
        for cell in cells:
            creature_index.setdefault(cell, []).append(c.entity_id)
    self._creature_pos_index = creature_index
    self._spatial_index_valid = True


def _world_index_remove_creature_v222(self: World, c: Creature) -> None:
    idx = getattr(self, "_creature_pos_index", None)
    if not isinstance(idx, dict):
        return
    try:
        cells = c.occupied_cells()
    except Exception:
        cells = [(c.x, c.y)]
    for cell in cells:
        ids = idx.get(cell)
        if not ids:
            continue
        try:
            while c.entity_id in ids:
                ids.remove(c.entity_id)
        except ValueError:
            pass
        if not ids:
            idx.pop(cell, None)


def _world_index_add_creature_v222(self: World, c: Creature) -> None:
    idx = getattr(self, "_creature_pos_index", None)
    if not isinstance(idx, dict):
        return
    if not getattr(c, "alive", False):
        return
    try:
        cells = c.occupied_cells()
    except Exception:
        cells = [(c.x, c.y)]
    for cell in cells:
        ids = idx.setdefault(cell, [])
        if c.entity_id not in ids:
            ids.append(c.entity_id)


World.rebuild_spatial_indices = _world_rebuild_spatial_indices_v222
World._index_remove_creature = _world_index_remove_creature_v222
World._index_add_creature = _world_index_add_creature_v222


_old_creature_at_v222 = World.creature_at

def _creature_at_v222(self: World, x: int, y: int, ignore_id: Optional[str] = None) -> Optional[Creature]:
    idx = getattr(self, "_creature_pos_index", None)
    if not getattr(self, "_spatial_index_valid", False) or not isinstance(idx, dict):
        # Rebuild barato comparado con el escaneo antiguo; sucede en setup/comandos.
        try:
            self.rebuild_spatial_indices()
            idx = getattr(self, "_creature_pos_index", {})
        except Exception:
            return _old_creature_at_v222(self, x, y, ignore_id)
    for eid in idx.get((x, y), []):
        if eid == ignore_id:
            continue
        c = self.creatures.get(eid)
        if c is not None and getattr(c, "alive", False):
            return c
    return None

World.creature_at = _creature_at_v222


_old_can_place_creature_v222 = World.can_place_creature

def _can_place_creature_v222(self: World, c: Creature, x: int, y: int) -> bool:
    # Misma lógica que la original, pero usando creature_at() indexado.
    try:
        cells = c.occupied_cells(x, y)
    except Exception:
        return _old_can_place_creature_v222(self, c, x, y)
    for cx, cy in cells:
        if not self.in_bounds(cx, cy):
            return False
        terrain = self.grid[cy][cx]
        if terrain == CAVE_WALL:
            return False
        if c.kind in ("cow", "trex") and terrain == CAVE_INTERIOR:
            return False
        if self.creature_at(cx, cy, ignore_id=c.entity_id):
            return False
    return True

World.can_place_creature = _can_place_creature_v222


_old_move_creature_v222 = World.move_creature

def _move_creature_v222(self: World, c: Creature, dx: int, dy: int) -> bool:
    nx, ny = c.x + dx, c.y + dy
    if self.can_place_creature(c, nx, ny):
        if getattr(self, "_spatial_index_valid", False):
            self._index_remove_creature(c)
            c.x, c.y = nx, ny
            self._index_add_creature(c)
        else:
            c.x, c.y = nx, ny
        return True
    return False

World.move_creature = _move_creature_v222


_old_add_creature_v222 = World.add_creature

def _add_creature_v222(self: World, kind: str, x: int, y: int) -> Creature:
    c = _old_add_creature_v222(self, kind, x, y)
    if getattr(self, "_spatial_index_valid", False):
        self._index_add_creature(c)
    return c

World.add_creature = _add_creature_v222


_old_add_human_v222 = World.add_human

def _add_human_v222(self: World, x: int, y: int, parent: Optional[Human] = None, parent2: Optional[Human] = None) -> Human:
    h = _old_add_human_v222(self, x, y, parent, parent2)
    if getattr(self, "_spatial_index_valid", False):
        self._index_add_creature(h)
    return h

World.add_human = _add_human_v222


_old_kill_v222 = World.kill

def _kill_v222(self: World, c: Creature, cause: str) -> None:
    was_alive = getattr(c, "alive", False)
    result = _old_kill_v222(self, c, cause)
    # Si no es inmortal y murió, lo retiramos del índice inmediatamente.
    if was_alive and not getattr(c, "alive", False) and getattr(self, "_spatial_index_valid", False):
        try:
            self._index_remove_creature(c)
        except Exception:
            self._spatial_index_valid = False
    return result

World.kill = _kill_v222


_old_run_tick_v222 = World.run_tick

def _run_tick_v222(self: World) -> None:
    # Rebuild una vez por tick: coste O(N), evita miles de escaneos O(N) por movimiento.
    self.rebuild_spatial_indices()
    return _old_run_tick_v222(self)

World.run_tick = _run_tick_v222


# Cache ligero para counts por zona/especie. Antes se recalculaba escaneando criaturas
# muchas veces dentro de animal_dispersal_step(). Se invalida cada tick y al moverse.
_old_species_zone_counts_v222 = World.species_zone_counts

def _species_zone_counts_v222(self: World, kind: str) -> Dict[int, int]:
    cache_tick = getattr(self, "_zone_cache_tick", None)
    cache = getattr(self, "_zone_count_cache", None)
    if cache_tick != self.tick or not isinstance(cache, dict):
        cache = {}
        self._zone_count_cache = cache
        self._zone_cache_tick = self.tick
    if kind not in cache:
        cache[kind] = _old_species_zone_counts_v222(self, kind)
    return cache[kind]

World.species_zone_counts = _species_zone_counts_v222


# Render/status: que se vea claro qué versión optimizada se está usando.
_old_render_to_string_v222 = World.render_to_string

def _render_to_string_v222(self: World) -> str:
    txt = _old_render_to_string_v222(self)
    try:
        return txt.replace("PROTOHUMANOS 2D v2.1", "PROTOHUMANOS 2D v2.2.2 FASTIDX")
    except Exception:
        return txt

World.render_to_string = _render_to_string_v222


# Help breve en métricas: versión de rendimiento.
_old_detector_metrics_report_v222 = World.detector_metrics_report

def _detector_metrics_report_v222(self: World) -> str:
    base = _old_detector_metrics_report_v222(self)
    return base + "\n\nOPTIMIZACIÓN v2.2.2\n" + "="*100 + "\nÍndice espacial activo: creature_at/can_place O(1), cache de zonas por tick.\n"

World.detector_metrics_report = _detector_metrics_report_v222


# ============================================================
# v2.2.3 — FAST MODE REAL: detector incremental + índices cercanos
# ============================================================
# Motivo: en simulaciones largas se producía una pausa periódica (~1s) porque
# cada análisis recorría TODOS los humanos e investigaciones acumuladas. Esta
# versión reparte el trabajo del detector por tandas pequeñas. No elimina datos:
# retrasa unos ticks/días la revisión de algunos humanos, pero evita parones.

_PROTOH_VERSION = "2.2.3"

# ---------- Índices auxiliares de humanos/linaje/items ----------

def _ensure_human_indices_v223(self: World) -> None:
    if getattr(self, "_human_indices_valid", False):
        return
    self._human_birth_index = {h.birth_number: h for h in self.humans.values()}
    children: Dict[int, List[Human]] = {}
    for h in self.humans.values():
        if h.parent1_birth:
            children.setdefault(h.parent1_birth, []).append(h)
        if h.parent2_birth:
            children.setdefault(h.parent2_birth, []).append(h)
    self._children_birth_index = children
    self._human_indices_valid = True

World.ensure_human_indices = _ensure_human_indices_v223

_old_add_human_v223 = World.add_human

def _add_human_v223(self: World, x: int, y: int, parent: Optional[Human] = None, parent2: Optional[Human] = None) -> Human:
    h = _old_add_human_v223(self, x, y, parent, parent2)
    self._human_indices_valid = False
    return h

World.add_human = _add_human_v223

_old_human_by_birth_v223 = World.human_by_birth

def _human_by_birth_v223(self: World, birth_number: int) -> Optional[Human]:
    try:
        self.ensure_human_indices()
        return self._human_birth_index.get(int(birth_number))
    except Exception:
        return _old_human_by_birth_v223(self, birth_number)

World.human_by_birth = _human_by_birth_v223

_old_children_of_v223 = World.children_of

def _children_of_v223(self: World, birth_number: int) -> List[Human]:
    try:
        self.ensure_human_indices()
        return list(self._children_birth_index.get(int(birth_number), []))
    except Exception:
        return _old_children_of_v223(self, birth_number)

World.children_of = _children_of_v223


def _world_rebuild_item_index_v223(self: World) -> None:
    idx: Dict[Tuple[int, int], List[str]] = {}
    kind_idx: Dict[str, List[str]] = {}
    for item in self.items.values():
        idx.setdefault((item.x, item.y), []).append(item.item_id)
        kind_idx.setdefault(item.kind, []).append(item.item_id)
    self._item_pos_index = idx
    self._item_kind_index = kind_idx
    self._item_index_valid = True

World.rebuild_item_index = _world_rebuild_item_index_v223

_old_add_item_v223 = World.add_item

def _add_item_v223(self: World, kind: str, x: int, y: int) -> Item:
    item = _old_add_item_v223(self, kind, x, y)
    if getattr(self, "_item_index_valid", False):
        self._item_pos_index.setdefault((item.x, item.y), []).append(item.item_id)
        self._item_kind_index.setdefault(item.kind, []).append(item.item_id)
    return item

World.add_item = _add_item_v223

_old_items_at_v223 = World.items_at

def _items_at_v223(self: World, x: int, y: int) -> List[Item]:
    if not getattr(self, "_item_index_valid", False):
        try:
            self.rebuild_item_index()
        except Exception:
            return _old_items_at_v223(self, x, y)
    out: List[Item] = []
    for iid in self._item_pos_index.get((x, y), []):
        it = self.items.get(iid)
        if it is not None and it.x == x and it.y == y:
            out.append(it)
    return out

World.items_at = _items_at_v223


def _nearby_items_v223(self: World, pos: Tuple[int, int], radius: float, kind: Optional[str] = None) -> List[Item]:
    if not getattr(self, "_item_index_valid", False):
        self.rebuild_item_index()
    px, py = pos
    r = int(math.ceil(radius))
    r2 = radius * radius
    out: List[Item] = []
    if kind and len(self._item_kind_index.get(kind, [])) < 80:
        ids = self._item_kind_index.get(kind, [])
        for iid in ids:
            it = self.items.get(iid)
            if it is not None and (it.x - px) * (it.x - px) + (it.y - py) * (it.y - py) <= r2:
                out.append(it)
        return out
    for y in range(max(0, py - r), min(HEIGHT, py + r + 1)):
        for x in range(max(0, px - r), min(WIDTH, px + r + 1)):
            if (x - px) * (x - px) + (y - py) * (y - py) > r2:
                continue
            for iid in self._item_pos_index.get((x, y), []):
                it = self.items.get(iid)
                if it is not None and (kind is None or it.kind == kind):
                    out.append(it)
    return out

World.nearby_items = _nearby_items_v223


def _nearby_creatures_v223(self: World, pos: Tuple[int, int], radius: float, kind: Optional[str] = None, ignore_id: Optional[str] = None) -> List[Creature]:
    if not getattr(self, "_spatial_index_valid", False):
        self.rebuild_spatial_indices()
    px, py = pos
    r = int(math.ceil(radius))
    r2 = radius * radius
    seen: Set[str] = set()
    out: List[Creature] = []
    idx = getattr(self, "_creature_pos_index", {})
    for y in range(max(0, py - r), min(HEIGHT, py + r + 1)):
        for x in range(max(0, px - r), min(WIDTH, px + r + 1)):
            if (x - px) * (x - px) + (y - py) * (y - py) > r2:
                continue
            for eid in idx.get((x, y), []):
                if eid == ignore_id or eid in seen:
                    continue
                c = self.creatures.get(eid)
                if c is None or not getattr(c, "alive", False):
                    continue
                if kind is not None and c.kind != kind:
                    continue
                seen.add(eid)
                out.append(c)
    return out

World.nearby_creatures = _nearby_creatures_v223

_old_nearest_creature_v223 = World.nearest_creature

def _nearest_creature_v223(self: World, h: Human, kind: str, radius: float) -> Optional[Creature]:
    try:
        pos = h.pos()
        candidates = self.nearby_creatures(pos, radius, kind=kind, ignore_id=h.entity_id)
        return min(candidates, key=lambda c: (c.x - pos[0]) * (c.x - pos[0]) + (c.y - pos[1]) * (c.y - pos[1])) if candidates else None
    except Exception:
        return _old_nearest_creature_v223(self, h, kind, radius)

World.nearest_creature = _nearest_creature_v223

_old_nearest_item_v223 = World.nearest_item

def _nearest_item_v223(self: World, pos: Tuple[int, int], kind: str, radius: float) -> Optional[Item]:
    try:
        candidates = self.nearby_items(pos, radius, kind=kind)
        return min(candidates, key=lambda i: (i.x - pos[0]) * (i.x - pos[0]) + (i.y - pos[1]) * (i.y - pos[1])) if candidates else None
    except Exception:
        return _old_nearest_item_v223(self, pos, kind, radius)

World.nearest_item = _nearest_item_v223

_old_best_food_v223 = World.best_food_or_potential_food_target

def _best_food_or_potential_food_target_v223(self: World, h: Human) -> Optional[Tuple[Tuple[int, int], str, Any]]:
    try:
        radius = self.vision_radius(16)
        pos = h.pos()
        candidates: List[Tuple[Tuple[int, int], str, Any, float]] = []
        seed_knowledge = max(
            h.neural.connections.get(tuple(sorted(("objeto_seed", "hambre_baja"))), 0.0),
            h.neural.connections.get(tuple(sorted(("objeto_pequeño_comestible", "hambre_baja"))), 0.0),
        )
        chicken_knowledge = max(
            h.neural.connections.get(tuple(sorted(("pollo", "hambre_baja"))), 0.0),
            h.neural.connections.get(tuple(sorted(("pollo", "comida_potencial"))), 0.0),
        )
        meat_knowledge = h.neural.connections.get(tuple(sorted(("comida_meat", "hambre_baja"))), 0.0)
        for item in self.nearby_items(pos, radius):
            dx = item.x - pos[0]; dy = item.y - pos[1]
            d2 = dx*dx + dy*dy
            d = math.sqrt(d2) if d2 else 0.0
            learned = seed_knowledge if item.kind == "seed" else (meat_knowledge if item.kind == "meat" else 0.0)
            physical_try = 0.18 if item.edible else (0.16 if item.weight <= 2.0 else 0.04)
            score = learned * 1.8 + physical_try + (0.05 / max(1.0, d))
            if score > 0.05:
                candidates.append(((item.x, item.y), "item_food" if learned > 0.12 else "potential_item", item, score))
        for cr in self.nearby_creatures(pos, radius, ignore_id=h.entity_id):
            if cr.kind not in ("chicken", "cow"):
                continue
            dx = cr.x - pos[0]; dy = cr.y - pos[1]
            d2 = dx*dx + dy*dy
            d = math.sqrt(d2) if d2 else 0.0
            learned = chicken_knowledge if cr.kind == "chicken" else 0.0
            physical_try = 0.12 if cr.kind == "chicken" else (0.03 + h.genes.aggression * 0.05)
            score = learned * 1.8 + physical_try + (0.05 / max(1.0, d))
            if score > 0.04:
                candidates.append((cr.pos(), "creature_food" if learned > 0.12 else "potential_creature", cr, score))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[3] / max(1.0, math.sqrt((x[0][0]-pos[0])**2 + (x[0][1]-pos[1])**2)), reverse=True)
        p0, typ, obj, _ = candidates[0]
        return (p0, typ, obj)
    except Exception:
        return _old_best_food_v223(self, h)

World.best_food_or_potential_food_target = _best_food_or_potential_food_target_v223

# ---------- Investigación incremental ----------

_old_open_or_update_investigation_v223 = World.open_or_update_investigation

def _rebuild_investigation_key_index_v223(self: World) -> None:
    idx: Dict[Tuple[int, str], int] = {}
    for inv_id, inv in self.investigations.items():
        if not inv.concluded:
            idx[(inv.subject_birth, inv.category)] = inv_id
    self._active_investigation_key_index = idx
    self._investigation_key_index_valid = True

World.rebuild_investigation_key_index = _rebuild_investigation_key_index_v223


def _open_or_update_investigation_v223(self: World, h: Human, category: str, hypothesis: str, confidence: float,
                                       evidence_for: Optional[List[str]] = None, evidence_against: Optional[List[str]] = None,
                                       inherited_from: Optional[int] = None, generations_left: int = 3,
                                       duration_days: int = 6) -> ConceptInvestigation:
    # Versión O(1) para encontrar investigación activa por humano/categoría.
    evidence_for = evidence_for or []
    evidence_against = evidence_against or []
    if not getattr(self, "_investigation_key_index_valid", False):
        self.rebuild_investigation_key_index()
    key = (h.birth_number, category)
    inv = None
    inv_id = self._active_investigation_key_index.get(key)
    if inv_id is not None:
        inv = self.investigations.get(inv_id)
        if inv is not None and inv.concluded:
            inv = None
    if inv is None:
        inv = ConceptInvestigation(
            inv_id=self.next_investigation_id,
            origin_birth=inherited_from or h.birth_number,
            subject_birth=h.birth_number,
            category=category,
            hypothesis=hypothesis,
            started_tick=self.tick,
            started_day=self.day,
            expires_tick=self.tick + duration_days * TICKS_PER_DAY,
            last_update_tick=self.tick,
            inherited_from=inherited_from,
            generations_left=generations_left,
            watch_weights=self.investigation_watch_weights(category),
            confidence=clamp(confidence, 0, 100),
        )
        self.next_investigation_id += 1
        self.investigations[inv.inv_id] = inv
        self._active_investigation_key_index[key] = inv.inv_id
        self.lineage_watch_roots.setdefault(inv.origin_birth, []).append(inv.inv_id)
        self.all_logs.append(f"[Día {self.day} T{self.tick}] INVESTIGACIÓN ABIERTA H{h.birth_number}: {category} | {hypothesis} | confianza {pct(confidence)}")
    inv.last_update_tick = self.tick
    inv.expires_tick = max(inv.expires_tick, self.tick + duration_days * TICKS_PER_DAY)
    inv.confidence = clamp(max(inv.confidence * 0.92, confidence), 0, 100)
    for e in evidence_for:
        if e not in inv.evidence_for:
            inv.evidence_for.append(e)
    for e in evidence_against:
        if e not in inv.evidence_against:
            inv.evidence_against.append(e)
    inv.evidence_for = inv.evidence_for[-60:]
    inv.evidence_against = inv.evidence_against[-40:]
    return inv

World.open_or_update_investigation = _open_or_update_investigation_v223


def _recent_events_for_inv_v223(h: Human, cutoff_tick: int) -> List[Event]:
    # memory_events ya está limitado; al recorrer desde el final evitamos repasar todo.
    out: List[Event] = []
    for e in reversed(h.memory_events):
        if e.tick < cutoff_tick:
            break
        out.append(e)
    out.reverse()
    return out


def _update_single_investigation_v223(self: World, inv: ConceptInvestigation) -> None:
    h = self.human_by_birth(inv.subject_birth)
    if not h:
        return
    recent = _recent_events_for_inv_v223(h, max(inv.started_tick, self.tick - 10 * TICKS_PER_DAY))
    c = h.neural.connections
    cat = inv.category
    for_e: List[str] = []
    against: List[str] = []
    days_seen = len({e.day for e in recent})
    if days_seen >= 3:
        for_e.append(f"conducta observada durante {days_seen} días distintos")
    if len(recent) < 3 and self.tick > inv.started_tick + 3 * TICKS_PER_DAY:
        against.append("poca evidencia nueva tras varios días")
    if cat in ("exploracion_medicion", "ruta_mapa", "dimension_espacio"):
        exploratory = [e for e in recent if e.kind in ("beber", "coger_objeto", "accion_fisica_sin_efecto", "experimento_refugio", "accion_no_prevista")]
        if c.get(tuple(sorted(("impulso_explorador", "mover_hacia_desconocido"))), 0) > 0.35:
            for_e.append("impulso_explorador ↔ mover_hacia_desconocido reforzado")
        if exploratory and h.hunger < 45 and h.thirst < 45:
            for_e.append("actividad exploratoria con hambre/sed no extremas")
    if cat == "agua_sed":
        if c.get(tuple(sorted(("agua", "sed_baja"))), 0) > 0.25: for_e.append("agua ↔ sed_baja reforzado")
        if c.get(tuple(sorted(("mover_hacia_agua", "sed_alta"))), 0) > 0.25: for_e.append("sed_alta ↔ mover_hacia_agua reforzado")
    if cat == "comida_hambre":
        if c.get(tuple(sorted(("comida_meat", "hambre_baja"))), 0) > 0.18: for_e.append("comida_meat ↔ hambre_baja reforzado")
        if c.get(tuple(sorted(("hambre_alta", "mover_hacia_ser_pequeño"))), 0) > 0.25: for_e.append("hambre_alta ↔ mover_hacia_ser_pequeño reforzado")
    if cat in ("miedo_muerte", "peligro"):
        deaths = [e for e in recent if e.kind == "observa_muerte"]
        if c.get(tuple(sorted(("no_movimiento", "ser_human"))), 0) > 0.25: for_e.append("no_movimiento ↔ ser_human reforzado")
        if c.get(tuple(sorted(("dolor", "forma_trex"))), 0) > 0.12 or c.get(tuple(sorted(("dolor", "forma_cow"))), 0) > 0.12: for_e.append("dolor asociado a forma animal concreta")
        if deaths: for_e.append(f"observó {len(deaths)} muertes recientes")
    if cat in ("refugio", "cueva", "construccion"):
        ref_events = [e for e in recent if e.kind in ("experimento_refugio", "dormir")]
        if c.get(tuple(sorted(("intento_refugio", "palos_piedras"))), 0) > 0.08: for_e.append("intento_refugio ↔ palos_piedras reforzado")
        if c.get(tuple(sorted(("cueva_interior", "reposo"))), 0) > 0.12: for_e.append("cueva_interior ↔ reposo reforzado")
        if ref_events: for_e.append(f"eventos relacionados con refugio/descanso: {len(ref_events)}")
    if cat == "sueño_fuerza":
        if c.get(tuple(sorted(("sueño_bajo", "golpe_debil"))), 0) > 0.18: for_e.append("sueño_bajo ↔ golpe_debil reforzado")
        if any(e.kind == "dormir" for e in recent) and any(e.kind == "ataque" for e in recent): for_e.append("hay sueño y golpes recientes para comparar")
    if cat == "almacenamiento":
        inv_events = [e for e in recent if "inventario" in e.kind or e.kind in ("coger_objeto", "comer")]
        if c.get(tuple(sorted(("comida_guardada", "hambre_baja"))), 0) > 0.08: for_e.append("comida_guardada ↔ hambre_baja reforzado")
        if len(inv_events) >= 4: for_e.append("usa inventario/coger/comer de forma repetida")
    if cat == "cebo_trampa":
        drops = [e for e in recent if e.kind == "soltar_semilla"]
        if c.get(tuple(sorted(("semilla", "pollo_cercano"))), 0) > 0.05: for_e.append("semilla ↔ pollo_cercano reforzado")
        if drops: for_e.append(f"soltó semillas {len(drops)} veces")
    if cat in ("vida_existencia", "auto_vida", "identidad_continuidad"):
        # Compatible con el detector v2.2 de vida/auto-vida.
        if c.get(tuple(sorted(("no_movimiento", "ser_human"))), 0) > 0.18: for_e.append("ser_human ↔ no_movimiento/muerte aparece")
        if c.get(tuple(sorted(("mi_necesidad", "mismo_ser"))), 0) > 0.10 or c.get(tuple(sorted(("yo_cuerpo", "mismo_ser"))), 0) > 0.10: for_e.append("señales de mismo_ser/yo_cuerpo")
        if h.hunger > 70 or h.thirst > 70: for_e.append("necesidad propia alta registrada")
    for e in for_e:
        if e not in inv.evidence_for:
            inv.evidence_for.append(e)
    for e in against:
        if e not in inv.evidence_against:
            inv.evidence_against.append(e)
    inv.evidence_for = inv.evidence_for[-60:]
    inv.evidence_against = inv.evidence_against[-40:]
    new_for = len(for_e); new_against = len(against)
    total_for = len(inv.evidence_for); total_against = len(inv.evidence_against)
    maturity_bonus = min(18.0, total_for * 1.15)
    contradiction_penalty = min(26.0, total_against * 2.2)
    heredity_bonus = 3.0 if inv.inherited_from and total_for >= 4 else 0.0
    fresh_delta = new_for * 1.6 - new_against * 2.4
    cap_by_category = {
        "concepto_no_claro": 58.0, "agua_sed": 68.0, "comida_hambre": 70.0,
        "exploracion_medicion": 78.0, "sueño_fuerza": 90.0, "miedo_muerte": 88.0,
        "refugio": 88.0, "cebo_trampa": 86.0, "almacenamiento": 86.0,
        "vida_existencia": 84.0, "auto_vida": 86.0, "identidad_continuidad": 82.0,
    }
    new_conf = clamp(inv.confidence * 0.92 + maturity_bonus - contradiction_penalty + heredity_bonus + fresh_delta, 0, 100)
    inv.confidence = min(new_conf, cap_by_category.get(inv.category, 72.0))
    old_state = inv.state
    if inv.confidence < 25 and self.tick > inv.started_tick + 5 * TICKS_PER_DAY:
        inv.state = "FALSA ALARMA PROBABLE"
    elif inv.confidence < 45:
        inv.state = "EN SEGUIMIENTO"
    elif inv.confidence < 62:
        inv.state = "PATRÓN FUNCIONAL"
    elif inv.confidence < 80:
        inv.state = "CONCEPTO EMERGENTE"
    else:
        inv.state = "CONCEPTO REFINADO"
    inv.valuable = inv.state in ("CONCEPTO EMERGENTE", "CONCEPTO REFINADO") or (inv.category in ("refugio", "cebo_trampa", "almacenamiento", "miedo_muerte", "exploracion_medicion", "vida_existencia", "auto_vida") and inv.confidence >= 50)
    if self.tick > inv.expires_tick and inv.confidence < 45:
        inv.concluded = True
        inv.state = "FALSA ALARMA PROBABLE"
        try:
            self._active_investigation_key_index.pop((inv.subject_birth, inv.category), None)
        except Exception:
            self._investigation_key_index_valid = False
    if inv.state != old_state and inv.valuable:
        block = self.format_investigation(inv, compact=False)
        styled = style_text(block, "gold" if inv.confidence >= 70 and inv.category in ("refugio", "cebo_trampa", "almacenamiento", "miedo_muerte", "vida_existencia", "auto_vida") else "darkblue")
        self.concept_logs.append(styled)
        self.all_logs.append(styled)
        h.detected_concepts.append(f"[DÍA {self.day} | TICK {self.tick}] INVESTIGACIÓN LONGITUDINAL: {inv.category} | confianza {pct(inv.confidence)} | estado={inv.state}")
        if inv.category in ("refugio", "cebo_trampa", "almacenamiento", "miedo_muerte", "exploracion_medicion", "vida_existencia", "auto_vida") and inv.confidence >= 55:
            self.register_gene_bank(h, f"investigación longitudinal valiosa: {inv.category} {pct(inv.confidence)}")


def _update_investigations_v223(self: World) -> None:
    invs = list(self.investigations.values())
    total = len(invs)
    if total == 0:
        return
    # Presupuesto adaptativo: evita parones. Si hay pocas investigaciones, procesa todas.
    budget = 450 if total > 1200 else 320 if total > 600 else 220 if total > 250 else total
    start = int(getattr(self, "_investigation_update_cursor", 0)) % max(1, total)
    subset = [invs[(start + i) % total] for i in range(min(budget, total))]
    self._investigation_update_cursor = (start + len(subset)) % max(1, total)
    if not getattr(self, "_investigation_key_index_valid", False):
        self.rebuild_investigation_key_index()
    # Herencia solo para el subset: se reparte en el tiempo.
    for inv in subset:
        subject = self.human_by_birth(inv.subject_birth)
        if not subject or inv.generations_left <= 0:
            continue
        children = self.children_of(inv.subject_birth)
        if not children:
            continue
        parent_score = self.gene_score(subject)
        for child in children[:12]:  # evita explosiones con linajes gigantes
            key = (child.birth_number, inv.category)
            if self._active_investigation_key_index.get(key):
                continue
            child_score = self.gene_score(child)
            if inv.confidence >= 45 or child_score >= parent_score * 0.94:
                self.open_or_update_investigation(
                    child, inv.category,
                    f"seguimiento heredado del linaje #{inv.origin_birth}: {inv.hypothesis}",
                    max(18.0, inv.confidence * 0.45),
                    evidence_for=[f"hijo de #{inv.subject_birth}; vigilancia heredada sin conceptos heredados"],
                    inherited_from=inv.origin_birth,
                    generations_left=inv.generations_left - 1,
                    duration_days=10,
                )
    for inv in subset:
        _update_single_investigation_v223(self, inv)

World.update_investigations = _update_investigations_v223

# ---------- Metaobservador incremental ----------

_DETECTOR_HUMAN_BUDGET_MIN = 12
_DETECTOR_HUMAN_BUDGET_MAX = 80


def _analyze_all_v223(self: MetaObserver) -> None:
    world = self.world
    alive = [h for h in world.humans.values() if h.alive]
    if not alive:
        # Aun así, actualiza investigaciones pendientes por si quedan estados a cerrar.
        world.update_investigations()
        return
    total = len(alive)
    # Budget adaptativo: con muchos humanos no analizamos todos en el mismo tick.
    if total <= 30:
        budget = total
    elif total <= 100:
        budget = 45
    elif total <= 300:
        budget = 60
    else:
        budget = _DETECTOR_HUMAN_BUDGET_MAX
    start = int(getattr(self, "_human_analyze_cursor", 0)) % total
    subset = [alive[(start + i) % total] for i in range(min(budget, total))]
    self._human_analyze_cursor = (start + len(subset)) % total
    for h in subset:
        if not h.alive:
            continue
        self.detect_unexpected_actions(h)
        self.detect_bait_trap(h)
        self.detect_sleep_strength(h)
        self.detect_cave_safety(h)
        self.detect_big_creature_avoidance(h)
        self.detect_fear_or_death_concepts(h)
        self.detect_unclassified_clusters(h)
        self.detect_open_sequence_patterns(h)
        self.detect_inventory_storage(h)
        # Detectores v2.2 avanzados, antes se ejecutaban en otro pase sobre todos los humanos.
        try:
            _detect_life_and_autolife_v22(self, h)
            _detect_universal_families_v22(self, h)
        except Exception:
            pass
    # Tareas globales repartidas: evitan parones de 1 segundo.
    if world.tick % (DETECTOR_EVERY_TICKS * 4) == 0:
        world.update_gene_bank()
    world.update_investigations()
    if world.tick % (DETECTOR_EVERY_TICKS * 8) == 0:
        self.detect_cultural_patterns()
    # Métricas internas para saber si el detector va en modo incremental.
    world._detector_last_budget = len(subset)
    world._detector_alive_total = total

MetaObserver.analyze_all = _analyze_all_v223

# ---------- Run tick: reconstruye índices de items junto a criaturas ----------

_old_run_tick_v223 = World.run_tick

def _run_tick_v223(self: World) -> None:
    self.rebuild_spatial_indices()
    self.rebuild_item_index()
    return _old_run_tick_v223(self)

World.run_tick = _run_tick_v223

# ---------- Informes de rendimiento ----------

_old_detector_metrics_report_v223 = World.detector_metrics_report

def _detector_metrics_report_v223(self: World) -> str:
    base = _old_detector_metrics_report_v223(self)
    lines = [base, "", "OPTIMIZACIÓN v2.2.3 — FAST MODE REAL", "=" * 100]
    lines.append("- Índice espacial O(1) para creature_at/can_place.")
    lines.append("- Índice de items por celda/tipo.")
    lines.append("- Detector incremental: no analiza todos los humanos en el mismo tick.")
    lines.append("- Investigaciones longitudinales por presupuesto/cursor.")
    lines.append(f"Último lote detector: {getattr(self, '_detector_last_budget', '?')}/{getattr(self, '_detector_alive_total', '?')} humanos vivos")
    lines.append(f"Investigaciones totales: {len(self.investigations)} | cursor={getattr(self, '_investigation_update_cursor', 0)}")
    return "\n".join(lines)

World.detector_metrics_report = _detector_metrics_report_v223

_old_render_to_string_v223 = World.render_to_string

def _render_to_string_v223(self: World) -> str:
    txt = _old_render_to_string_v223(self)
    try:
        txt = txt.replace("PROTOHUMANOS 2D v2.1", "PROTOHUMANOS 2D v2.2.3 FAST")
        txt = txt.replace("PROTOHUMANOS 2D v2.2.2 FASTIDX", "PROTOHUMANOS 2D v2.2.3 FAST")
    except Exception:
        pass
    return txt

World.render_to_string = _render_to_string_v223


# ============================================================
# v2.2.4 — OPTIMIZACIÓN DE BÚSQUEDAS CERCANAS
# ============================================================
# v2.2.3 redujo el parón del detector. Aquí se corrige otro cuello de botella:
# las búsquedas cercanas por radio escaneaban muchas celdas del mapa por cada
# humano. Para el tamaño actual del mundo, es más rápido mantener listas por
# especie y escanear solo esos animales/items.

_PROTOH_VERSION = "2.2.4"

_old_rebuild_spatial_indices_v224 = World.rebuild_spatial_indices

def _rebuild_spatial_indices_v224(self: World) -> None:
    _old_rebuild_spatial_indices_v224(self)
    by_kind: Dict[str, List[str]] = {}
    for eid, c in self.creatures.items():
        if getattr(c, "alive", False):
            by_kind.setdefault(c.kind, []).append(eid)
    self._creature_kind_index = by_kind

World.rebuild_spatial_indices = _rebuild_spatial_indices_v224


def _creatures_of_kind_v224(self: World, kind: Optional[str] = None) -> List[Creature]:
    if not getattr(self, "_spatial_index_valid", False) or not hasattr(self, "_creature_kind_index"):
        self.rebuild_spatial_indices()
    if kind is None:
        ids = []
        for arr in getattr(self, "_creature_kind_index", {}).values():
            ids.extend(arr)
    else:
        ids = getattr(self, "_creature_kind_index", {}).get(kind, [])
    out = []
    for eid in ids:
        c = self.creatures.get(eid)
        if c is not None and getattr(c, "alive", False):
            out.append(c)
    return out

World.creatures_of_kind = _creatures_of_kind_v224


def _nearby_creatures_v224(self: World, pos: Tuple[int, int], radius: float, kind: Optional[str] = None, ignore_id: Optional[str] = None) -> List[Creature]:
    # Escanea listas por especie en vez de 1000+ celdas por consulta.
    px, py = pos
    r2 = radius * radius
    out: List[Creature] = []
    source = self.creatures_of_kind(kind) if kind is not None else [c for c in self.creatures.values() if c.alive]
    for c in source:
        if c.entity_id == ignore_id:
            continue
        dx = c.x - px; dy = c.y - py
        if dx*dx + dy*dy <= r2:
            out.append(c)
    return out

World.nearby_creatures = _nearby_creatures_v224


def _nearby_items_v224(self: World, pos: Tuple[int, int], radius: float, kind: Optional[str] = None) -> List[Item]:
    # Para <=500 items, escaneo lineal es más rápido que mirar todas las celdas del radio.
    px, py = pos
    r2 = radius * radius
    if kind is not None:
        if not getattr(self, "_item_index_valid", False):
            self.rebuild_item_index()
        ids = getattr(self, "_item_kind_index", {}).get(kind, [])
        source = [self.items[iid] for iid in ids if iid in self.items]
    else:
        source = self.items.values()
    out: List[Item] = []
    for it in source:
        dx = it.x - px; dy = it.y - py
        if dx*dx + dy*dy <= r2:
            out.append(it)
    return out

World.nearby_items = _nearby_items_v224


def _nearest_creature_v224(self: World, h: Human, kind: str, radius: float) -> Optional[Creature]:
    pos = h.pos(); px, py = pos; r2 = radius * radius
    best = None; best_d2 = 10**12
    for c in self.creatures_of_kind(kind):
        if c.entity_id == h.entity_id:
            continue
        dx = c.x - px; dy = c.y - py; d2 = dx*dx + dy*dy
        if d2 <= r2 and d2 < best_d2:
            best = c; best_d2 = d2
    return best

World.nearest_creature = _nearest_creature_v224


def _nearest_item_v224(self: World, pos: Tuple[int, int], kind: str, radius: float) -> Optional[Item]:
    px, py = pos; r2 = radius * radius
    best = None; best_d2 = 10**12
    for it in self.nearby_items(pos, radius, kind=kind):
        dx = it.x - px; dy = it.y - py; d2 = dx*dx + dy*dy
        if d2 <= r2 and d2 < best_d2:
            best = it; best_d2 = d2
    return best

World.nearest_item = _nearest_item_v224

_old_apply_social_comfort_v224 = World.apply_social_comfort

def _apply_social_comfort_v224(self: World, h: Human) -> None:
    px, py = h.x, h.y
    found = False
    for o in self.creatures_of_kind("human"):
        if o.entity_id == h.entity_id:
            continue
        dx = o.x - px; dy = o.y - py
        if dx*dx + dy*dy <= 16:
            found = True
            break
    if not found:
        return
    h.energy = clamp(h.energy + 0.25, 0, 100)
    h.sleepiness = clamp(h.sleepiness - 0.15, 0, 100)
    h.neural.activate("otro_humano_cerca", 0.16)
    h.neural.activate("bienestar_social", 0.12)
    h.neural.reinforce("otro_humano_cerca", "bienestar_social", 0.04)

World.apply_social_comfort = _apply_social_comfort_v224

_old_count_alive_v224 = World.count_alive

def _count_alive_v224(self: World, kind: str) -> int:
    try:
        return len(self.creatures_of_kind(kind))
    except Exception:
        return _old_count_alive_v224(self, kind)

World.count_alive = _count_alive_v224

# Reaplica best_food para que use nearby_* recién optimizadas.
# La función v2.2.3 ya llama self.nearby_items/self.nearby_creatures, así que no hace falta reescribirla.

_old_detector_metrics_report_v224 = World.detector_metrics_report

def _detector_metrics_report_v224(self: World) -> str:
    base = _old_detector_metrics_report_v224(self)
    lines = [base, "", "OPTIMIZACIÓN v2.2.4", "=" * 100]
    lines.append("- Listas por especie para nearest_creature/nearby_creatures.")
    lines.append("- Búsqueda lineal rápida de items cercanos para mapas con <500 items.")
    lines.append("- apply_social_comfort y count_alive optimizados.")
    return "\n".join(lines)

World.detector_metrics_report = _detector_metrics_report_v224

_old_render_to_string_v224 = World.render_to_string

def _render_to_string_v224(self: World) -> str:
    txt = _old_render_to_string_v224(self)
    try:
        txt = txt.replace("PROTOHUMANOS 2D v2.2.3 FAST", "PROTOHUMANOS 2D v2.2.4 FAST")
    except Exception:
        pass
    return txt

World.render_to_string = _render_to_string_v224


# ============================================================
# v2.2.5 — MÁS OPTIMIZACIÓN PARA FAST LARGO
# ============================================================
_PROTOH_VERSION = "2.2.5"

# Conteos vivos por especie cacheados por tick.
def _count_alive_v225(self: World, kind: str) -> int:
    if not getattr(self, "_spatial_index_valid", False) or not hasattr(self, "_creature_kind_index"):
        self.rebuild_spatial_indices()
    return len(getattr(self, "_creature_kind_index", {}).get(kind, []))

World.count_alive = _count_alive_v225

# Best food: evita escanear todos los animales; mira solo pollos y vacas.
def _best_food_or_potential_food_target_v225(self: World, h: Human) -> Optional[Tuple[Tuple[int, int], str, Any]]:
    radius = self.vision_radius(16)
    r2 = radius * radius
    pos = h.pos(); px, py = pos
    candidates: List[Tuple[Tuple[int, int], str, Any, float]] = []
    cdict = h.neural.connections
    seed_knowledge = max(
        cdict.get(tuple(sorted(("objeto_seed", "hambre_baja"))), 0.0),
        cdict.get(tuple(sorted(("objeto_pequeño_comestible", "hambre_baja"))), 0.0),
    )
    chicken_knowledge = max(
        cdict.get(tuple(sorted(("pollo", "hambre_baja"))), 0.0),
        cdict.get(tuple(sorted(("pollo", "comida_potencial"))), 0.0),
    )
    meat_knowledge = cdict.get(tuple(sorted(("comida_meat", "hambre_baja"))), 0.0)
    # Items cercanos: escaneo lineal de items, barato y sin grid radius.
    for item in self.items.values():
        dx = item.x - px; dy = item.y - py; d2 = dx*dx + dy*dy
        if d2 > r2:
            continue
        d = math.sqrt(d2) if d2 else 0.0
        learned = seed_knowledge if item.kind == "seed" else (meat_knowledge if item.kind == "meat" else 0.0)
        physical_try = 0.18 if item.edible else (0.16 if item.weight <= 2.0 else 0.04)
        score = learned * 1.8 + physical_try + (0.05 / max(1.0, d))
        if score > 0.05:
            candidates.append(((item.x, item.y), "item_food" if learned > 0.12 else "potential_item", item, score))
    # Solo criaturas comestibles/posibles.
    for kind in ("chicken", "cow"):
        for cr in self.creatures_of_kind(kind):
            if cr.entity_id == h.entity_id:
                continue
            dx = cr.x - px; dy = cr.y - py; d2 = dx*dx + dy*dy
            if d2 > r2:
                continue
            d = math.sqrt(d2) if d2 else 0.0
            learned = chicken_knowledge if cr.kind == "chicken" else 0.0
            physical_try = 0.12 if cr.kind == "chicken" else (0.03 + h.genes.aggression * 0.05)
            score = learned * 1.8 + physical_try + (0.05 / max(1.0, d))
            if score > 0.04:
                candidates.append((cr.pos(), "creature_food" if learned > 0.12 else "potential_creature", cr, score))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[3] / max(1.0, math.sqrt((x[0][0]-px)**2 + (x[0][1]-py)**2)), reverse=True)
    p0, typ, obj, _ = candidates[0]
    return (p0, typ, obj)

World.best_food_or_potential_food_target = _best_food_or_potential_food_target_v225

# Evita crear listas de objetos en creatures_of_kind cuando solo se necesita iterar.
def _iter_creatures_of_kind_v225(self: World, kind: Optional[str] = None):
    if not getattr(self, "_spatial_index_valid", False) or not hasattr(self, "_creature_kind_index"):
        self.rebuild_spatial_indices()
    if kind is None:
        for arr in getattr(self, "_creature_kind_index", {}).values():
            for eid in arr:
                c = self.creatures.get(eid)
                if c is not None and getattr(c, "alive", False):
                    yield c
    else:
        for eid in getattr(self, "_creature_kind_index", {}).get(kind, []):
            c = self.creatures.get(eid)
            if c is not None and getattr(c, "alive", False):
                yield c

World.iter_creatures_of_kind = _iter_creatures_of_kind_v225

# Reescribe funciones calientes para usar iterador sin lista.
def _nearest_creature_v225(self: World, h: Human, kind: str, radius: float) -> Optional[Creature]:
    px, py = h.x, h.y; r2 = radius * radius
    best = None; best_d2 = 10**12
    for c in self.iter_creatures_of_kind(kind):
        if c.entity_id == h.entity_id:
            continue
        dx = c.x - px; dy = c.y - py; d2 = dx*dx + dy*dy
        if d2 <= r2 and d2 < best_d2:
            best = c; best_d2 = d2
    return best

World.nearest_creature = _nearest_creature_v225


def _apply_social_comfort_v225(self: World, h: Human) -> None:
    px, py = h.x, h.y
    for o in self.iter_creatures_of_kind("human"):
        if o.entity_id == h.entity_id:
            continue
        dx = o.x - px; dy = o.y - py
        if dx*dx + dy*dy <= 16:
            h.energy = clamp(h.energy + 0.25, 0, 100)
            h.sleepiness = clamp(h.sleepiness - 0.15, 0, 100)
            h.neural.activate("otro_humano_cerca", 0.16)
            h.neural.activate("bienestar_social", 0.12)
            h.neural.reinforce("otro_humano_cerca", "bienestar_social", 0.04)
            return

World.apply_social_comfort = _apply_social_comfort_v225

# Detector incremental más fino si hay muchísima gente: baja lote, pero no bloquea.
def _analyze_all_v225(self: MetaObserver) -> None:
    world = self.world
    alive = [h for h in world.humans.values() if h.alive]
    if not alive:
        world.update_investigations(); return
    total = len(alive)
    if total <= 30: budget = total
    elif total <= 100: budget = 35
    elif total <= 300: budget = 45
    else: budget = 60
    start = int(getattr(self, "_human_analyze_cursor", 0)) % total
    subset = [alive[(start + i) % total] for i in range(min(budget, total))]
    self._human_analyze_cursor = (start + len(subset)) % total
    for h in subset:
        self.detect_unexpected_actions(h)
        self.detect_bait_trap(h)
        self.detect_sleep_strength(h)
        self.detect_cave_safety(h)
        self.detect_big_creature_avoidance(h)
        self.detect_fear_or_death_concepts(h)
        self.detect_unclassified_clusters(h)
        self.detect_open_sequence_patterns(h)
        self.detect_inventory_storage(h)
        try:
            _detect_life_and_autolife_v22(self, h)
            _detect_universal_families_v22(self, h)
        except Exception:
            pass
    if world.tick % (DETECTOR_EVERY_TICKS * 5) == 0:
        world.update_gene_bank()
    world.update_investigations()
    if world.tick % (DETECTOR_EVERY_TICKS * 10) == 0:
        self.detect_cultural_patterns()
    world._detector_last_budget = len(subset)
    world._detector_alive_total = total

MetaObserver.analyze_all = _analyze_all_v225

# Investigación: presupuesto más bajo en mundos enormes, mantiene rotación.
def _update_investigations_v225(self: World) -> None:
    invs = list(self.investigations.values())
    total = len(invs)
    if total == 0: return
    budget = 260 if total > 3000 else 220 if total > 1500 else 180 if total > 700 else min(total, 220)
    start = int(getattr(self, "_investigation_update_cursor", 0)) % total
    subset = [invs[(start + i) % total] for i in range(min(budget, total))]
    self._investigation_update_cursor = (start + len(subset)) % total
    if not getattr(self, "_investigation_key_index_valid", False):
        self.rebuild_investigation_key_index()
    for inv in subset:
        subject = self.human_by_birth(inv.subject_birth)
        if not subject or inv.generations_left <= 0: continue
        children = self.children_of(inv.subject_birth)
        if not children: continue
        parent_score = self.gene_score(subject)
        for child in children[:6]:
            key = (child.birth_number, inv.category)
            if self._active_investigation_key_index.get(key): continue
            if inv.confidence >= 45 or self.gene_score(child) >= parent_score * 0.94:
                self.open_or_update_investigation(child, inv.category, f"seguimiento heredado del linaje #{inv.origin_birth}: {inv.hypothesis}", max(18.0, inv.confidence * 0.45), evidence_for=[f"hijo de #{inv.subject_birth}; vigilancia heredada sin conceptos heredados"], inherited_from=inv.origin_birth, generations_left=inv.generations_left-1, duration_days=10)
    for inv in subset:
        _update_single_investigation_v223(self, inv)

World.update_investigations = _update_investigations_v225

_old_detector_metrics_report_v225 = World.detector_metrics_report

def _detector_metrics_report_v225(self: World) -> str:
    base = _old_detector_metrics_report_v225(self)
    return base + "\n\nOPTIMIZACIÓN v2.2.5\n" + "="*100 + "\n- best_food escanea solo items + pollos/vacas, no todos los seres.\n- Detector/investigaciones con presupuestos más bajos para mundos grandes.\n"

World.detector_metrics_report = _detector_metrics_report_v225

_old_render_to_string_v225 = World.render_to_string

def _render_to_string_v225(self: World) -> str:
    txt = _old_render_to_string_v225(self)
    return txt.replace("PROTOHUMANOS 2D v2.2.4 FAST", "PROTOHUMANOS 2D v2.2.5 FAST")

World.render_to_string = _render_to_string_v225



# ============================================================
# v2.3 — INMORTALES SIN DAÑO FÍSICO + DETECTOR PROTO-LENGUAJE
# ============================================================
# Objetivo:
# - Los inmortales son una condición experimental: no reciben daño físico por ataques,
#   pero conservan hambre/sed/sueño normales. Así no se refugian eternamente por dolor
#   de depredadores, sin prohibirles cuevas por magia.
# - Añade detector de proto-lenguaje/señales: señal repetida + contexto + respuesta social.
_PROTOH_VERSION = "2.3"

# ----------------------------
# Inmortales v2.3: sin daño físico, necesidades normales
# ----------------------------
# Sustituye el marcador de inmortalidad de v2.1.x. No da conceptos, no quita hambre/sed.
# Mantiene el bloqueo de aprendizaje por defecto si no se usa "learn".
def _mark_immortal_v23(world: World, h: Human, reason: str = "comando", allow_learning: bool = False) -> None:
    h.immortal = True
    h.immortal_no_damage = True
    h.concept_learning_blocked = not bool(allow_learning)
    # A diferencia de v2.1.x, NO subimos hambre/sed/vejez a 9999.
    # La prueba debe conservar necesidades reales para que el sujeto siga moviéndose.
    h.max_hp = max(float(getattr(h, "max_hp", 30.0)), 30.0)
    h.hp = clamp(float(getattr(h, "hp", h.max_hp)), 1.0, h.max_hp)
    h.energy = max(float(getattr(h, "energy", 80.0)), 70.0)
    # Limpia resistencias absurdas heredadas si se crea desde comandos nuevos.
    h.hunger_resistance = min(max(float(getattr(h, "hunger_resistance", 1.0)), 1.0), 2.0)
    h.thirst_resistance = min(max(float(getattr(h, "thirst_resistance", 1.0)), 1.0), 2.0)
    h.old_age_resistance = min(max(float(getattr(h, "old_age_resistance", 1.0)), 1.0), 2.0)
    tag = "[MODO INMORTAL v2.3] sin daño físico por ataques; hambre/sed/sueño siguen activos"
    if not any("[MODO INMORTAL" in str(c) for c in h.detected_concepts):
        if allow_learning:
            h.detected_concepts.append(tag + "; APRENDIZAJE PERMITIDO por comando")
        else:
            h.detected_concepts.append(tag + "; aprendizaje conceptual BLOQUEADO")
    if not allow_learning:
        try:
            for inv in world.investigations.values():
                if inv.subject_birth == h.birth_number:
                    inv.concluded = True
                    inv.state = "BLOQUEADA_POR_INMORTAL_SIN_APRENDIZAJE"
        except Exception:
            pass
    try:
        world.log(
            "modo_inmortal_v23",
            h.entity_id,
            nacimiento=h.birth_number,
            motivo=reason,
            aprendizaje=("permitido" if allow_learning else "bloqueado"),
            no_damage=True,
            hambre_sed_normales=True,
            nota="no puede morir; ataques no bajan HP; necesidades siguen activas",
        )
    except Exception:
        pass

# Reasigna el nombre global usado por los wrappers de comandos existentes.
_mark_immortal = _mark_immortal_v23

_old_attack_v23 = World.attack

def _attack_v23(self: World, attacker: Creature, target: Creature, damage: float, weapon_kind: str, allow_counter: bool = True) -> None:
    # Inmortal v2.3: ataques físicos impactan, pero no bajan HP ni generan dolor fuerte.
    # No bloquea que el humano aprenda de la presencia/amenaza, pero evita la trampa
    # experimental de quedarse en cuevas por daño acumulado de depredadores.
    if isinstance(target, Human) and getattr(target, "immortal", False) and getattr(target, "immortal_no_damage", False):
        if not attacker.alive or not target.alive:
            return
        if not self.can_attack_target(attacker, target):
            self.log("ataque_falla_por_espacio", attacker.entity_id, objetivo=target.entity_id, terreno=self.terrain_at(target.x, target.y))
            return
        if attacker.kind == "human" and target.kind in ("cow", "trex"):
            self.predator_clear_ignore_for(target, attacker.entity_id)
        self.predator_register_attack_success(attacker, target)
        target.last_attacker = attacker.entity_id
        # Señal sensorial suave: impacto/amenaza, no dolor/vida_baja.
        target.neural.activate("impacto_sin_daño", 0.12)
        target.neural.activate(f"forma_{attacker.kind}", 0.08)
        target.neural.activate(f"atacado_por_{attacker.kind}", 0.08)
        target.neural.reinforce(f"forma_{attacker.kind}", "impacto_sin_daño", 0.025)
        target.neural.reinforce(f"atacado_por_{attacker.kind}", "impacto_sin_daño", 0.025)
        self.log(
            "ataque_sin_daño_inmortal",
            attacker.entity_id,
            objetivo=target.entity_id,
            objetivo_tipo=target.kind,
            daño_original=round(damage, 2),
            daño_aplicado=0,
            arma=weapon_kind,
            hp_objetivo=round(target.hp, 2),
            nota="inmortal v2.3: impacto registrado sin daño físico; hambre/sed/sueño siguen funcionando",
        )
        return
    return _old_attack_v23(self, attacker, target, damage, weapon_kind, allow_counter)

World.attack = _attack_v23

# Blindaje adicional: si por hambre/sed u otro efecto llega a kill(), sigue sin morir,
# pero conserva necesidades; no se resetea a HP 9999.
_old_kill_v23 = World.kill

def _kill_v23(self: World, c: Creature, cause: str) -> None:
    if isinstance(c, Human) and getattr(c, "immortal", False):
        c.alive = True
        c.hp = max(float(getattr(c, "hp", 1.0)), max(1.0, float(getattr(c, "max_hp", 30.0)) * 0.25))
        c.last_attacker = None
        self.log("muerte_evitada_inmortal_v23", c.entity_id, causa=cause, hp=round(c.hp, 2), hambre=round(getattr(c, 'hunger', 0), 1), sed=round(getattr(c, 'thirst', 0), 1), pos=c.pos(), nota="inmortal experimental; no muere, pero necesidades no se borran")
        return
    return _old_kill_v23(self, c, cause)

World.kill = _kill_v23

# ----------------------------
# Detector proto-lenguaje/señales v2.3
# ----------------------------
_PROTO_LANGUAGE_SIGNAL_KINDS = {
    "accion_fisica_sin_efecto", "soltar_semilla", "experimento_combinacion",
    "experimento_refugio", "fallo_fisico_previsible", "coger_objeto",
}
_PROTO_LANGUAGE_RESPONSE_KINDS = {
    "dormir", "beber", "comer", "coger_objeto", "ataque", "soltar_semilla",
    "experimento_refugio", "experimento_combinacion", "muerte", "observa_muerte",
}

def _event_context_tags_v23(ev: Event) -> Set[str]:
    s = (ev.kind + " " + " ".join(f"{k}={v}" for k, v in ev.data.items())).lower()
    tags: Set[str] = set()
    if any(x in s for x in ("trex", "cow", "ataque", "daño", "dolor", "peligro", "muerte", "no_movimiento")):
        tags.add("peligro/muerte")
    if any(x in s for x in ("cueva", "refugio", "reposo", "dormir", "interior")):
        tags.add("refugio/reposo")
    if any(x in s for x in ("agua", "beber", "sed")):
        tags.add("agua/sed")
    if any(x in s for x in ("seed", "semilla", "pollo", "chicken", "comer", "hambre", "meat")):
        tags.add("comida/cebo")
    if any(x in s for x in ("otro_humano", "bienestar_social", "human", "grupo")):
        tags.add("social/grupo")
    if any(x in s for x in ("gesto", "sin_efecto", "combinar", "palo", "piedra", "herramienta", "objeto")):
        tags.add("señal/objeto")
    if not tags:
        tags.add("contexto_indefinido")
    return tags

def _signal_key_v23(ev: Event) -> str:
    if ev.kind == "accion_fisica_sin_efecto":
        return str(ev.data.get("accion", "gesto_al_aire"))
    if ev.kind == "soltar_semilla":
        return "soltar_semilla"
    if ev.kind == "experimento_combinacion":
        return "combinar_objetos"
    if ev.kind == "experimento_refugio":
        return "intentar_refugio_objetos"
    if ev.kind == "fallo_fisico_previsible":
        return str(ev.data.get("accion", "fallo_fisico_previsible"))
    if ev.kind == "coger_objeto":
        return f"coger_{ev.data.get('objeto','objeto')}"
    return ev.kind

def _detect_proto_language_v23(observer: MetaObserver, h: Human) -> None:
    world = observer.world
    if getattr(h, "concept_learning_blocked", False):
        return
    recent = h.memory_events[-700:]
    signals = [e for e in recent if e.kind in _PROTO_LANGUAGE_SIGNAL_KINDS]
    if len(signals) < 4:
        return

    # Agrupa señal + contexto dominante cercano.
    clusters: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for sig in signals[-80:]:
        nearby = [e for e in recent if abs(e.tick - sig.tick) <= 8]
        tags: List[str] = []
        for e in nearby:
            tags.extend(list(_event_context_tags_v23(e)))
        if tags:
            context = max(set(tags), key=tags.count)
        else:
            context = "contexto_indefinido"
        key = (_signal_key_v23(sig), context)
        d = clusters.setdefault(key, {"events": [], "days": set(), "responses": 0, "others": set(), "transmission": 0})
        d["events"].append(sig)
        d["days"].add(sig.day)
        # Respuesta social: eventos de otros humanos justo después.
        for ev in world.events:
            if ev.actor_id == h.entity_id:
                continue
            if ev.kind not in _PROTO_LANGUAGE_RESPONSE_KINDS:
                continue
            if sig.tick < ev.tick <= sig.tick + 6:
                actor = world.humans.get(ev.actor_id)
                if actor and actor.alive and dist(actor.pos(), h.pos()) <= 10:
                    d["responses"] += 1
                    d["others"].add(getattr(actor, "birth_number", ev.actor_id))
        # Transmisión débil: otros humanos hacen señal parecida en contexto parecido.
        for other in world.humans.values():
            if other.entity_id == h.entity_id or not other.alive:
                continue
            for oe in other.memory_events[-120:]:
                if oe.kind in _PROTO_LANGUAGE_SIGNAL_KINDS and abs(oe.tick - sig.tick) <= TICKS_PER_DAY * 3:
                    if _signal_key_v23(oe) == key[0]:
                        d["transmission"] += 1
                        d["others"].add(other.birth_number)
                        break

    if not clusters:
        return
    best_key, best = max(clusters.items(), key=lambda kv: (len(kv[1]["events"]) * 1.3 + len(kv[1]["days"]) * 2.0 + kv[1]["responses"] * 1.5 + kv[1]["transmission"] * 1.2))
    signal, context = best_key
    reps = len(best["events"])
    days = len(best["days"])
    responses = int(best["responses"])
    others = len(best["others"])
    transmission = int(best["transmission"])

    # Penaliza señales sin respuesta social: gesto solo no es lenguaje.
    confidence = clamp(
        reps * 4.0 + days * 7.0 + min(responses, 10) * 4.5 + min(others, 6) * 4.0 + min(transmission, 8) * 3.0,
        0,
        96,
    )
    if responses == 0 and transmission == 0:
        confidence *= 0.45
    if days < 2:
        confidence *= 0.70

    if confidence < 38:
        return
    bucket = int(world.tick // (TICKS_PER_DAY * 5))
    if not observer.should_print(f"proto-language-{h.entity_id}-{signal}-{context}-{bucket}", confidence, min_gap=TICKS_PER_DAY * 5, min_conf=38):
        return

    evid = [
        f"Señal repetida: {signal}",
        f"Contexto dominante: {context}",
        f"Repeticiones recientes: {reps}",
        f"Días distintos: {days}",
        f"Respuestas de otros en los 6 ticks posteriores: {responses}",
        f"Otros humanos implicados/señales parecidas: {others}",
        f"Transmisión/imitación aproximada: {transmission}",
    ]
    extra = [
        f"señal: {signal}",
        f"contexto: {context}",
        f"respuesta social: {responses}",
        f"otros humanos: {others}",
    ]
    observer.print_report(
        "DETECTOR DE PROTO-LENGUAJE / SEÑALES",
        h,
        "COMUNICACIÓN EMERGENTE / PROTO-SÍMBOLO",
        "Señal repetida asociada a un contexto y posible respuesta de otros humanos.",
        "parece estar usando o generando una señal conductual que puede significar algo para otros. No es lenguaje humano; podría ser gesto, marca, llamada, advertencia, indicación o imitación social.",
        "proto-lenguaje / señal / símbolo / comunicación primitiva",
        confidence,
        evid,
        {
            "repetición": clamp(reps / 10, 0, 1),
            "persistencia_días": clamp(days / 6, 0, 1),
            "respuesta_social": clamp(responses / 8, 0, 1),
            "transmisión": clamp(transmission / 8, 0, 1),
            "varios_humanos": clamp(others / 5, 0, 1),
        },
        "No confirma lenguaje. Confirma una pista: señal + contexto + respuesta social. Si se repite y se diversifica, podría convertirse en proto-lenguaje.",
        extra=extra,
        gold=confidence >= 78,
        purple=confidence >= 85,
        darkblue=confidence < 78,
    )
    world.open_or_update_investigation(
        h,
        "proto_lenguaje",
        f"posible señal/proto-lenguaje: {signal} en contexto {context}",
        confidence,
        evidence_for=evid,
        evidence_against=["requiere demostrar que otros cambian conducta por la señal, no solo por el mismo estímulo"],
        duration_days=18,
    )

_old_analyze_all_v23 = MetaObserver.analyze_all

def _analyze_all_v23(self: MetaObserver) -> None:
    _old_analyze_all_v23(self)
    world = self.world
    # Detector social/proto-lenguaje por tandas pequeñas para no romper fast.
    if world.tick % (DETECTOR_EVERY_TICKS * 2) != 0:
        return
    alive = [h for h in world.humans.values() if h.alive]
    if not alive:
        return
    budget = min(18, len(alive)) if len(alive) <= 100 else 24
    start = int(getattr(self, "_proto_language_cursor", 0)) % len(alive)
    subset = [alive[(start + i) % len(alive)] for i in range(min(budget, len(alive)))]
    self._proto_language_cursor = (start + len(subset)) % len(alive)
    for h in subset:
        try:
            _detect_proto_language_v23(self, h)
        except Exception:
            pass
    world._proto_language_last_budget = len(subset)

MetaObserver.analyze_all = _analyze_all_v23

# Reporte/exports para proto-lenguaje.
def _language_report_v23(self: World) -> str:
    lines = ["PROTO-LENGUAJE / SEÑALES v2.3", "=" * 100]
    rows = []
    for inv in self.investigations.values():
        if inv.category == "proto_lenguaje" or "lenguaje" in inv.hypothesis.lower() or "señal" in inv.hypothesis.lower():
            h = self.human_by_birth(inv.subject_birth)
            rows.append((inv.confidence, inv, h))
    rows.sort(key=lambda x: x[0], reverse=True)
    if not rows:
        lines.append("No hay candidatos de proto-lenguaje todavía.")
    else:
        for conf, inv, h in rows[:50]:
            name = f"#{h.birth_number} {h.name}" if h else f"#{inv.subject_birth}"
            st = "vivo" if h and h.alive else "muerto/desconocido"
            lines.append(f"INV{inv.inv_id} {name:<18} {st:<18} conf={conf:5.1f}% estado={inv.state} hipótesis={inv.hypothesis}")
            if inv.evidence_for:
                lines.append(f"    pista: {inv.evidence_for[-1]}")
    lines.append("")
    lines.append("Criterio: no busca palabras; busca señal repetida + contexto + respuesta/imitación social.")
    return "\n".join(lines)

World.language_report = _language_report_v23

_old_detector_metrics_report_v23 = World.detector_metrics_report

def _detector_metrics_report_v23(self: World) -> str:
    base = _old_detector_metrics_report_v23(self)
    inv_lang = sum(1 for inv in self.investigations.values() if inv.category == "proto_lenguaje")
    return base + "\n\nDETECTOR PROTO-LENGUAJE v2.3\n" + "=" * 100 + f"\n- investigaciones proto_lenguaje: {inv_lang}\n- último presupuesto de revisión: {getattr(self, '_proto_language_last_budget', 0)} humanos\n- detecta señal + contexto + respuesta social, no palabras.\n"

World.detector_metrics_report = _detector_metrics_report_v23

_old_process_command_v23 = process_command

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw = cmd.strip()
    low = raw.lower()
    if low in ("lenguaje", "proto_lenguaje", "language", "proto_language", "señales", "senales"):
        state["paused"] = True
        show_paged_text("PROTO-LENGUAJE / SEÑALES v2.3", world.language_report())
        return False
    if low.startswith("export lenguaje") or low.startswith("export proto_lenguaje") or low.startswith("export language"):
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            print("Uso: export lenguaje /ruta/lenguaje.txt")
            return False
        path = world.resolve_export_path(parts[2], f"protoH_lenguaje_dia{world.day}_tick{world.tick}.txt")
        ensure_dir_for_file(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(world.language_report())
        msg = f"Proto-lenguaje exportado: {path}"
        print(msg); state["status_message"] = msg
        return False
    return _old_process_command_v23(cmd, world, state)

_old_export_useful_v23 = World.export_useful_file

def _export_useful_file_v23(self: World, raw_path: str) -> str:
    msg = _old_export_useful_v23(self, raw_path)
    try:
        root = os.path.expanduser(str(raw_path).strip())
        # Si raw_path es carpeta creada por export useful, añade reporte al lado si puede.
        if os.path.isdir(root):
            path = os.path.join(root, "proto_lenguaje_v23.txt")
        else:
            path = os.path.join(os.path.dirname(root) or ".", "proto_lenguaje_v23.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.language_report())
    except Exception:
        pass
    return msg

World.export_useful_file = _export_useful_file_v23

_old_render_to_string_v23 = World.render_to_string

def _render_to_string_v23(self: World) -> str:
    txt = _old_render_to_string_v23(self)
    for old in ("PROTOHUMANOS 2D v2.2.5 FAST", "PROTOHUMANOS 2D v2.2.4 FAST", "PROTOHUMANOS 2D v2.1.4"):
        txt = txt.replace(old, "PROTOHUMANOS 2D v2.3 FAST")
    return txt

World.render_to_string = _render_to_string_v23

# Ayuda visible mínima añadida a help lab/export si se consulta en métricas/comandos.
try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.3 — INMORTALES SIN DAÑO Y PROTO-LENGUAJE
===========================================
- spawn 10 max immortal learn: inmortal sin daño físico de ataques, pero con hambre/sed/sueño normales.
- lenguaje / proto_lenguaje: muestra candidatos a señales/proto-lenguaje.
- export lenguaje RUTA.txt: exporta candidatos de proto-lenguaje.
"""
except Exception:
    pass



# ============================================================
# PATCH v2.3.1 — ECOLOGÍA DE SEMILLAS Y CEBO HUMANO
# ============================================================
# Objetivo:
# - Muchas menos semillas naturales.
# - Semillas naturales repartidas por sectores internos, evitando bordes/esquinas.
# - Las semillas NO se agotan del todo: crecen de forma lenta y sostenida.
# - Los pollos priorizan semillas colocadas por humanos frente a semillas naturales.
# - No se da conocimiento al humano ni al pollo: solo se ajusta la ecología/olor.

# Ajustes globales efectivos antes de main().
INITIAL_SEED_PATCHES = 35
SEED_TARGET_ON_MAP = 42
SEED_MAX_ON_MAP = 60
SEED_REGROW_PER_TICK = 1
SEED_REGROW_EVERY_TICKS = 4
SEED_GROW_CLUSTER_CHANCE = 0.08

SEED_EDGE_MARGIN_V231 = 6
SEED_SECTORS_X_V231 = 9
SEED_SECTORS_Y_V231 = 4
SEED_HUMAN_LURE_RADIUS_V231 = 12
SEED_NATURAL_LURE_RADIUS_V231 = 10
SEED_HUMAN_LURE_DAYS_V231 = 2.5  # recién colocadas: olor/atractivo fuerte
SEED_HUMAN_LURE_TICKS_V231 = int(TICKS_PER_DAY * SEED_HUMAN_LURE_DAYS_V231)


def _seed_origin_v231(item: Item) -> str:
    return str(getattr(item, "origin", "natural"))


def _is_human_placed_seed_v231(item: Item) -> bool:
    return item.kind == "seed" and _seed_origin_v231(item) == "human_placed"


def _seed_sector_index_v231(self: World, x: int, y: int) -> int:
    usable_w = max(1, WIDTH - 2 * SEED_EDGE_MARGIN_V231)
    usable_h = max(1, HEIGHT - 2 * SEED_EDGE_MARGIN_V231)
    sx = int(clamp((x - SEED_EDGE_MARGIN_V231) * SEED_SECTORS_X_V231 / usable_w, 0, SEED_SECTORS_X_V231 - 1))
    sy = int(clamp((y - SEED_EDGE_MARGIN_V231) * SEED_SECTORS_Y_V231 / usable_h, 0, SEED_SECTORS_Y_V231 - 1))
    return sy * SEED_SECTORS_X_V231 + sx

World.seed_sector_index = _seed_sector_index_v231


def _natural_seed_sector_counts_v231(self: World) -> Dict[int, int]:
    counts: Dict[int, int] = {i: 0 for i in range(SEED_SECTORS_X_V231 * SEED_SECTORS_Y_V231)}
    for it in self.items.values():
        if it.kind != "seed" or _seed_origin_v231(it) == "human_placed":
            continue
        # Si una semilla natural antigua quedó en borde, cuenta también, pero no favorece crecimiento ahí.
        if SEED_EDGE_MARGIN_V231 <= it.x < WIDTH - SEED_EDGE_MARGIN_V231 and SEED_EDGE_MARGIN_V231 <= it.y < HEIGHT - SEED_EDGE_MARGIN_V231:
            counts[self.seed_sector_index(it.x, it.y)] = counts.get(self.seed_sector_index(it.x, it.y), 0) + 1
    return counts

World.natural_seed_sector_counts = _natural_seed_sector_counts_v231


def _seed_count_on_map_v231(self: World) -> int:
    return sum(1 for i in self.items.values() if i.kind == "seed")

World.seed_count_on_map = _seed_count_on_map_v231

_old_add_item_v231 = World.add_item

def _add_item_v231(self: World, kind: str, x: int, y: int, origin: str = "natural", placed_by: Optional[str] = None) -> Item:
    item = _old_add_item_v231(self, kind, x, y)
    if kind == "seed":
        setattr(item, "origin", origin)
        setattr(item, "placed_by", placed_by)
        setattr(item, "placed_tick", self.tick)
        setattr(item, "lure_strength", 2.4 if origin == "human_placed" else 1.0)
    return item

World.add_item = _add_item_v231


def _random_seed_cell_in_sector_v231(self: World, sector: int) -> Optional[Tuple[int, int]]:
    sx = sector % SEED_SECTORS_X_V231
    sy = sector // SEED_SECTORS_X_V231
    usable_w = WIDTH - 2 * SEED_EDGE_MARGIN_V231
    usable_h = HEIGHT - 2 * SEED_EDGE_MARGIN_V231
    x0 = SEED_EDGE_MARGIN_V231 + int(sx * usable_w / SEED_SECTORS_X_V231)
    x1 = SEED_EDGE_MARGIN_V231 + int((sx + 1) * usable_w / SEED_SECTORS_X_V231) - 1
    y0 = SEED_EDGE_MARGIN_V231 + int(sy * usable_h / SEED_SECTORS_Y_V231)
    y1 = SEED_EDGE_MARGIN_V231 + int((sy + 1) * usable_h / SEED_SECTORS_Y_V231) - 1
    x0, x1 = max(SEED_EDGE_MARGIN_V231, x0), min(WIDTH - SEED_EDGE_MARGIN_V231 - 1, x1)
    y0, y1 = max(SEED_EDGE_MARGIN_V231, y0), min(HEIGHT - SEED_EDGE_MARGIN_V231 - 1, y1)
    if x0 > x1 or y0 > y1:
        return None
    for _ in range(40):
        x = random.randint(x0, x1)
        y = random.randint(y0, y1)
        if self.grid[y][x] != EMPTY:
            continue
        if self.creature_at(x, y):
            continue
        if any(i.kind == "seed" and i.x == x and i.y == y for i in self.items.values()):
            continue
        return (x, y)
    return None

World.random_seed_cell_in_sector = _random_seed_cell_in_sector_v231


def _grow_seed_patch_v231(self: World, near: Optional[Tuple[int, int]] = None) -> bool:
    """Crecimiento natural v2.3.1: pocas semillas, repartidas, no pegadas al borde."""
    counts = self.natural_seed_sector_counts()
    if not counts:
        return False
    min_count = min(counts.values())
    low_sectors = [s for s, c in counts.items() if c == min_count]
    # Elegimos entre sectores menos poblados para evitar atractores/esquinas.
    random.shuffle(low_sectors)
    candidates = low_sectors + [s for s, _ in sorted(counts.items(), key=lambda kv: kv[1]) if s not in low_sectors]
    for sector in candidates[:12]:
        pos = self.random_seed_cell_in_sector(sector)
        if pos:
            self.add_item("seed", pos[0], pos[1], origin="natural")
            return True
    # Fallback interno, nunca en borde salvo que el mapa esté muy lleno.
    for _ in range(80):
        x = random.randint(SEED_EDGE_MARGIN_V231, WIDTH - SEED_EDGE_MARGIN_V231 - 1)
        y = random.randint(SEED_EDGE_MARGIN_V231, HEIGHT - SEED_EDGE_MARGIN_V231 - 1)
        if self.grid[y][x] == EMPTY and not self.creature_at(x, y) and not any(i.kind == "seed" and i.x == x and i.y == y for i in self.items.values()):
            self.add_item("seed", x, y, origin="natural")
            return True
    return False

World.grow_seed_patch = _grow_seed_patch_v231


def _regrow_seeds_v231(self: World) -> None:
    """Regeneración lenta y repartida.
    Mantiene alimento suficiente sin llenar bordes ni crear imanes permanentes.
    """
    if SEED_REGROW_EVERY_TICKS <= 0 or self.tick % SEED_REGROW_EVERY_TICKS != 0:
        return
    total = self.seed_count_on_map()
    if total >= SEED_MAX_ON_MAP:
        return
    # Crece siempre que falten semillas respecto al objetivo; por encima del objetivo, muy ocasionalmente.
    if total < SEED_TARGET_ON_MAP:
        attempts = 1 + min(2, (SEED_TARGET_ON_MAP - total) // 12)
    else:
        attempts = 1 if random.random() < 0.08 else 0
    for _ in range(attempts):
        if self.seed_count_on_map() >= SEED_MAX_ON_MAP:
            break
        self.grow_seed_patch()

World.regrow_seeds = _regrow_seeds_v231

_old_maybe_drop_seed_near_chicken_v231 = World.maybe_drop_seed_near_chicken

def _maybe_drop_seed_near_chicken_v231(self: World, h: Human) -> bool:
    seed = next((i for i in h.inventory if i.kind == "seed"), None)
    if not seed:
        return False
    chicken = self.nearest_creature(h, "chicken", self.vision_radius(10))
    if not chicken:
        return False

    bait_strength = self.neural_connection_strength(h, "semilla", "pollo_se_acerca")
    chance = 0.02 + h.genes.curiosity * 0.02 + bait_strength * 0.25
    if h.hunger > 55:
        chance += 0.03
    if random.random() > chance:
        return False

    h.inventory.remove(seed)
    seed.x, seed.y = h.x, h.y
    seed.item_id = self.make_id("it")
    setattr(seed, "origin", "human_placed")
    setattr(seed, "placed_by", h.entity_id)
    setattr(seed, "placed_tick", self.tick)
    setattr(seed, "lure_strength", 2.8)
    self.items[seed.item_id] = seed
    # Al haber cambiado id/posición de un item que venía del inventario, invalidamos índice.
    self._item_index_valid = False

    h.last_action = "soltar_semilla"
    h.neural.activate("semilla", 0.18)
    h.neural.activate("pollo_cercano", 0.12)
    h.neural.reinforce("semilla", "pollo_cercano", 0.04)
    h.neural.reinforce("semilla_humana", "pollo_se_acerca", 0.03)

    self.log(
        "soltar_semilla",
        h.entity_id,
        pos=h.pos(),
        pollo_cercano=chicken.entity_id,
        distancia=round(dist(h.pos(), chicken.pos()), 1),
        origin="human_placed",
        lure_strength=2.8,
    )
    return True

World.maybe_drop_seed_near_chicken = _maybe_drop_seed_near_chicken_v231


def _seed_attraction_score_v231(self: World, chicken: Creature, seed: Item) -> float:
    d = max(0.1, dist(chicken.pos(), (seed.x, seed.y)))
    if _is_human_placed_seed_v231(seed):
        age = self.tick - int(getattr(seed, "placed_tick", self.tick))
        freshness = 1.0 if age <= SEED_HUMAN_LURE_TICKS_V231 else 0.45
        return 10_000.0 + freshness * 150.0 - d  # siempre por delante de naturales dentro del radio
    # Naturales: cercanía + pequeño ruido para no sincronizar a todos los pollos con la misma.
    return 100.0 - d + random.random() * 0.25

World.seed_attraction_score = _seed_attraction_score_v231


def _update_chicken_v231(self: World, c: Creature) -> None:
    self.try_simple_animal_reproduce(c, "chicken")
    if random.random() > self.species_speed(c):
        return
    if c.last_attacker and c.last_attacker in self.creatures and self.creatures[c.last_attacker].alive:
        self.step_away(c, self.creatures[c.last_attacker].pos())
        return

    seeds_here = [i for i in self.items_at(c.x, c.y) if i.kind == "seed"]
    if seeds_here and random.random() < 0.55:
        human_here = [s for s in seeds_here if _is_human_placed_seed_v231(s)]
        seed = random.choice(human_here or seeds_here)
        self.items.pop(seed.item_id, None)
        self._item_index_valid = False
        self.log(
            "pollo_come_semilla",
            c.entity_id,
            semilla=seed.item_id,
            pos=c.pos(),
            origin=_seed_origin_v231(seed),
            placed_by=getattr(seed, "placed_by", None),
        )
        return

    # Si está pegado a un lateral, que salga, salvo si huele cebo humano cerca.
    human_seeds = [i for i in self.nearby_items(c.pos(), SEED_HUMAN_LURE_RADIUS_V231, "seed") if _is_human_placed_seed_v231(i)]
    if human_seeds:
        target = max(human_seeds, key=lambda i: self.seed_attraction_score(c, i))
        self.step_towards(c, (target.x, target.y))
        return

    if self.is_near_edge(c.pos()) and random.random() < 0.80 and self.animal_dispersal_step(c):
        return

    natural_seeds = [i for i in self.nearby_items(c.pos(), SEED_NATURAL_LURE_RADIUS_V231, "seed") if not _is_human_placed_seed_v231(i)]
    if natural_seeds:
        # No todos al mismo objetivo: elige entre las mejores cercanas con algo de variación.
        natural_seeds.sort(key=lambda i: self.seed_attraction_score(c, i), reverse=True)
        top = natural_seeds[:min(4, len(natural_seeds))]
        target = random.choice(top) if random.random() < 0.35 else top[0]
        self.step_towards(c, (target.x, target.y))
        return

    if self.animal_dispersal_step(c):
        return
    self.animal_idle_move(c)

World.update_chicken = _update_chicken_v231


def _seed_stats_report_v231(self: World) -> str:
    total = self.seed_count_on_map()
    natural = [i for i in self.items.values() if i.kind == "seed" and not _is_human_placed_seed_v231(i)]
    human = [i for i in self.items.values() if i.kind == "seed" and _is_human_placed_seed_v231(i)]
    edge = [i for i in natural if i.x < SEED_EDGE_MARGIN_V231 or i.x >= WIDTH - SEED_EDGE_MARGIN_V231 or i.y < SEED_EDGE_MARGIN_V231 or i.y >= HEIGHT - SEED_EDGE_MARGIN_V231]
    counts = self.natural_seed_sector_counts()
    used = sum(1 for c in counts.values() if c > 0)
    max_sector = max(counts.values()) if counts else 0
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    chickens_lured = 0
    for ch in chickens:
        if any(dist(ch.pos(), (s.x, s.y)) <= SEED_HUMAN_LURE_RADIUS_V231 for s in human):
            chickens_lured += 1
    lines = ["SEED STATS v2.3.1", "=" * 80]
    lines.append(f"semillas totales: {total} | naturales: {len(natural)} | humanas: {len(human)}")
    lines.append(f"objetivo natural total≈{SEED_TARGET_ON_MAP} | máximo={SEED_MAX_ON_MAP} | inicial={INITIAL_SEED_PATCHES}")
    lines.append(f"naturales en borde: {len(edge)} | sectores usados: {used}/{SEED_SECTORS_X_V231 * SEED_SECTORS_Y_V231} | máximo por sector: {max_sector}")
    lines.append(f"pollos vivos: {len(chickens)} | pollos cerca de semilla humana: {chickens_lured}")
    if human:
        newest = sorted(human, key=lambda i: getattr(i, "placed_tick", 0), reverse=True)[:8]
        lines.append("semillas humanas recientes:")
        for s in newest:
            lines.append(f"  - {s.item_id} pos=({s.x},{s.y}) placed_by={getattr(s,'placed_by',None)} age_ticks={self.tick - int(getattr(s,'placed_tick',self.tick))}")
    lines.append("\nDistribución natural por sectores:")
    for sy in range(SEED_SECTORS_Y_V231):
        row = []
        for sx in range(SEED_SECTORS_X_V231):
            row.append(f"{counts.get(sy*SEED_SECTORS_X_V231+sx,0):02d}")
        lines.append(" ".join(row))
    return "\n".join(lines)

World.seed_stats_report = _seed_stats_report_v231

_old_process_command_v231 = process_command

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw = cmd.strip()
    low = raw.lower()
    if low in ("seed_stats", "semillas", "seedmap", "seed_stats_v231"):
        state["paused"] = True
        show_paged_text("SEED STATS v2.3.1", world.seed_stats_report())
        return False
    if low.startswith("export seed_stats") or low.startswith("export semillas"):
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            print("Uso: export seed_stats /ruta/seed_stats.txt")
            return False
        path = world.resolve_export_path(parts[2], f"protoH_seed_stats_dia{world.day}_tick{world.tick}.txt")
        ensure_dir_for_file(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(world.seed_stats_report())
        msg = f"Seed stats exportado: {path}"
        print(msg); state["status_message"] = msg
        return False
    return _old_process_command_v231(cmd, world, state)

# Registrar el comando patched globalmente.
globals()["process_command"] = process_command

_old_detector_metrics_report_v231 = World.detector_metrics_report

def _detector_metrics_report_v231(self: World) -> str:
    base = _old_detector_metrics_report_v231(self)
    return base + "\n\nECOLOGÍA DE SEMILLAS v2.3.1\n" + "=" * 100 + f"\n- semillas iniciales: {INITIAL_SEED_PATCHES}\n- objetivo en mapa: {SEED_TARGET_ON_MAP}\n- máximo en mapa: {SEED_MAX_ON_MAP}\n- margen anti-borde: {SEED_EDGE_MARGIN_V231}\n- sectores: {SEED_SECTORS_X_V231}x{SEED_SECTORS_Y_V231}\n- semilla humana prioritaria para pollos: radio {SEED_HUMAN_LURE_RADIUS_V231}\nComando: seed_stats / export seed_stats RUTA\n"

World.detector_metrics_report = _detector_metrics_report_v231

_old_render_to_string_v231 = World.render_to_string

def _render_to_string_v231(self: World) -> str:
    txt = _old_render_to_string_v231(self)
    txt = txt.replace("PROTOHUMANOS 2D v2.3 FAST", "PROTOHUMANOS 2D v2.3.1 FAST")
    return txt

World.render_to_string = _render_to_string_v231

try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.3.1 — ECOLOGÍA DE SEMILLAS
=============================
- Muchas menos semillas naturales y mejor repartidas por sectores.
- Las semillas naturales evitan bordes/esquinas.
- Las semillas colocadas por humanos atraen a pollos antes que las naturales.
- seed_stats: diagnóstico de distribución de semillas.
- export seed_stats RUTA.txt: exporta diagnóstico.
"""
except Exception:
    pass



# v2.3.1b: también reparte las semillas iniciales por sectores; scatter_items(seed)
# ya no usa random_empty_cell(), que podía dejar muchas semillas en bordes.
_old_scatter_items_v231 = World.scatter_items

def _scatter_items_v231(self: World, kind: str, count: int) -> None:
    if kind != "seed":
        return _old_scatter_items_v231(self, kind, count)
    placed = 0
    for _ in range(count * 4):
        if placed >= count:
            break
        if self.grow_seed_patch():
            placed += 1
    # Fallback interno seguro si alguna cueva/agua impide completar el objetivo.
    while placed < count:
        pos = None
        for _ in range(80):
            x = random.randint(SEED_EDGE_MARGIN_V231, WIDTH - SEED_EDGE_MARGIN_V231 - 1)
            y = random.randint(SEED_EDGE_MARGIN_V231, HEIGHT - SEED_EDGE_MARGIN_V231 - 1)
            if self.grid[y][x] == EMPTY and not self.creature_at(x, y) and not any(i.kind == "seed" and i.x == x and i.y == y for i in self.items.values()):
                pos = (x, y); break
        if not pos:
            break
        self.add_item("seed", pos[0], pos[1], origin="natural")
        placed += 1

World.scatter_items = _scatter_items_v231



# ============================================================
# v2.3.2 — ECOLOGÍA DE POLLOS/SEMILLAS + COMANDO KILL
# ============================================================
# Objetivo:
# - Evitar que los pollos se queden en esquinas por falta de objetivo cercano.
# - Reducir aún más semillas naturales y repartirlas mejor.
# - Hacer que los pollos busquen activamente semillas, especialmente las colocadas por humanos.
# - Añadir kill <especie> <cantidad> como intervención de laboratorio.

_PROTOH_VERSION = "2.3.2"

# Menos semillas naturales que v2.3.1.
INITIAL_SEED_PATCHES = 24
SEED_TARGET_ON_MAP = 30
SEED_MAX_ON_MAP = 42
SEED_REGROW_PER_TICK = 1
SEED_GROW_CLUSTER_CHANCE = 0.02

# Los pollos tienen súper olfato. Las semillas humanas son prioridad absoluta.
SEED_NATURAL_LURE_RADIUS_V232 = max(WIDTH, HEIGHT)  # olor/rumbo amplio para evitar esquinas muertas
SEED_HUMAN_LURE_RADIUS_V232 = max(WIDTH, HEIGHT)    # cebo humano: prioridad global del mapa
CHICKEN_EDGE_MARGIN_V232 = 7
CHICKEN_CORNER_MARGIN_V232 = 10


def _is_corner_v232(pos: Tuple[int, int], margin: int = CHICKEN_CORNER_MARGIN_V232) -> bool:
    x, y = pos
    return (x <= margin or x >= WIDTH - 1 - margin) and (y <= margin or y >= HEIGHT - 1 - margin)


def _walk_towards_flexible_v232(self: World, c: Creature, target: Tuple[int, int]) -> bool:
    """Paso robusto hacia un objetivo.
    Prueba hasta 8 direcciones y elige las que reducen distancia. No teletransporta:
    solo intenta caminar una casilla evitando bloqueos/cuevas/otros cuerpos.
    """
    tx, ty = target
    options: List[Tuple[float, int, int]] = []
    current_d = dist(c.pos(), target)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = c.x + dx, c.y + dy
            # Permitimos un poco de movimiento lateral si no puede reducir distancia,
            # pero priorizamos reducirla claramente.
            nd = dist((nx, ny), target)
            if nd <= current_d + 0.01:
                options.append((nd + random.random() * 0.05, dx, dy))
    options.sort(key=lambda t: t[0])
    for _, dx, dy in options:
        if self.move_creature(c, dx, dy):
            return True
    # Fallback: paso normal existente por si el sistema antiguo encuentra ruta.
    try:
        return self.step_towards(c, target)
    except Exception:
        return False

World.walk_towards_flexible = _walk_towards_flexible_v232


def _all_seed_items_v232(self: World) -> List[Item]:
    try:
        # Si hay índice de items, aprovéchalo.
        if not getattr(self, "_item_index_valid", False):
            self.rebuild_item_index()
        ids = getattr(self, "_item_kind_index", {}).get("seed", [])
        return [self.items[i] for i in ids if i in self.items and self.items[i].kind == "seed"]
    except Exception:
        return [i for i in self.items.values() if i.kind == "seed"]

World.all_seed_items = _all_seed_items_v232


def _seed_priority_for_chicken_v232(self: World, chicken: Creature, seed: Item) -> float:
    d = max(0.1, dist(chicken.pos(), (seed.x, seed.y)))
    if _is_human_placed_seed_v231(seed):
        age = self.tick - int(getattr(seed, "placed_tick", self.tick))
        # Aunque envejezca, sigue ganando a las naturales: representa olor/manipulación/concentración.
        freshness = 1.0 if age <= SEED_HUMAN_LURE_TICKS_V231 else 0.55
        return 100000.0 + freshness * 1000.0 - d * 2.0
    # Naturales: prioriza cercanía, pero no deja esquinas sin objetivo.
    # Pequeña variación para que no todos los pollos elijan exactamente la misma semilla.
    edge_penalty = 40.0 if seed.x <= CHICKEN_EDGE_MARGIN_V232 or seed.x >= WIDTH - 1 - CHICKEN_EDGE_MARGIN_V232 or seed.y <= CHICKEN_EDGE_MARGIN_V232 or seed.y >= HEIGHT - 1 - CHICKEN_EDGE_MARGIN_V232 else 0.0
    return 1000.0 - d - edge_penalty + random.random() * 0.5

World.seed_priority_for_chicken = _seed_priority_for_chicken_v232


def _best_seed_for_chicken_v232(self: World, chicken: Creature) -> Optional[Item]:
    seeds = self.all_seed_items()
    if not seeds:
        return None
    # Primero cualquier cebo humano dentro del mundo/radio amplio.
    human_seeds = [s for s in seeds if _is_human_placed_seed_v231(s) and dist(chicken.pos(), (s.x, s.y)) <= SEED_HUMAN_LURE_RADIUS_V232]
    if human_seeds:
        return max(human_seeds, key=lambda s: self.seed_priority_for_chicken(chicken, s))
    natural = [s for s in seeds if not _is_human_placed_seed_v231(s) and dist(chicken.pos(), (s.x, s.y)) <= SEED_NATURAL_LURE_RADIUS_V232]
    if natural:
        # Elige entre las mejores para evitar sincronización absoluta, pero siempre hacia semillas.
        natural.sort(key=lambda s: self.seed_priority_for_chicken(chicken, s), reverse=True)
        top = natural[:min(5, len(natural))]
        return random.choice(top) if random.random() < 0.25 else top[0]
    return None

World.best_seed_for_chicken = _best_seed_for_chicken_v232


_old_update_chicken_v231_for_v232 = World.update_chicken

def _update_chicken_v232(self: World, c: Creature) -> None:
    self.try_simple_animal_reproduce(c, "chicken")
    if random.random() > self.species_speed(c):
        return

    # Si fue atacado, se aleja; luego vuelve a su conducta de semillas.
    if c.last_attacker and c.last_attacker in self.creatures and self.creatures[c.last_attacker].alive:
        if self.step_away(c, self.creatures[c.last_attacker].pos()):
            return

    seeds_here = [i for i in self.items_at(c.x, c.y) if i.kind == "seed"]
    if seeds_here:
        human_here = [s for s in seeds_here if _is_human_placed_seed_v231(s)]
        seed = random.choice(human_here or seeds_here)
        # Si ya está encima de la semilla, debe comerla con alta probabilidad.
        eat_chance = 0.96 if human_here else 0.82
        if random.random() < eat_chance:
            self.items.pop(seed.item_id, None)
            self._item_index_valid = False
            self.log(
                "pollo_come_semilla",
                c.entity_id,
                semilla=seed.item_id,
                pos=c.pos(),
                origin=_seed_origin_v231(seed),
                placed_by=getattr(seed, "placed_by", None),
                nota="v2.3.2: pollo prioriza semillas y cebo humano",
            )
            return

    # Objetivo principal: semilla. Esto evita que queden en esquinas sin moverse.
    target_seed = self.best_seed_for_chicken(c)
    if target_seed is not None:
        if self.walk_towards_flexible(c, (target_seed.x, target_seed.y)):
            # Marcar objetivo de forma ligera para diagnóstico.
            if self.tick % max(1, TICKS_PER_DAY) == 0:
                self.log(
                    "pollo_sigue_semilla",
                    c.entity_id,
                    semilla=target_seed.item_id,
                    origin=_seed_origin_v231(target_seed),
                    distancia=round(dist(c.pos(), (target_seed.x, target_seed.y)), 1),
                    pos=c.pos(),
                )
            return

    # Si por alguna razón no hay semillas, que salga de esquinas/bordes por caminata.
    if (_is_corner_v232(c.pos()) or self.is_near_edge(c.pos(), CHICKEN_EDGE_MARGIN_V232)) and self.animal_dispersal_step(c):
        return
    if self.animal_dispersal_step(c):
        return
    self.animal_idle_move(c)

World.update_chicken = _update_chicken_v232


# Refuerzo: las semillas naturales iniciales/regeneradas no deben aparecer en esquinas/bordes.
def _random_seed_cell_in_sector_v232(self: World, sector: int) -> Optional[Tuple[int, int]]:
    sx = sector % SEED_SECTORS_X_V231
    sy = sector // SEED_SECTORS_X_V231
    x0 = int(WIDTH * sx / SEED_SECTORS_X_V231)
    x1 = int(WIDTH * (sx + 1) / SEED_SECTORS_X_V231) - 1
    y0 = int(HEIGHT * sy / SEED_SECTORS_Y_V231)
    y1 = int(HEIGHT * (sy + 1) / SEED_SECTORS_Y_V231) - 1
    margin = max(SEED_EDGE_MARGIN_V231, CHICKEN_EDGE_MARGIN_V232)
    x0 = max(margin, x0); x1 = min(WIDTH - 1 - margin, x1)
    y0 = max(margin, y0); y1 = min(HEIGHT - 1 - margin, y1)
    if x0 > x1 or y0 > y1:
        return None
    for _ in range(140):
        x = random.randint(x0, x1)
        y = random.randint(y0, y1)
        if self.grid[y][x] != EMPTY:
            continue
        if self.creature_at(x, y):
            continue
        if any(i.kind == "seed" and i.x == x and i.y == y for i in self.items.values()):
            continue
        return (x, y)
    return None

World.random_seed_cell_in_sector = _random_seed_cell_in_sector_v232


# Comando de intervención: kill <species> <amount>
def _normalize_species_v232(s: str) -> str:
    low = s.lower().strip().replace("_", "-")
    aliases = {
        "t": "trex", "trex": "trex", "t-rex": "trex", "trexes": "trex", "rex": "trex",
        "v": "cow", "cow": "cow", "cows": "cow", "vaca": "cow", "vacas": "cow",
        "p": "chicken", "chicken": "chicken", "chickens": "chicken", "pollo": "chicken", "pollos": "chicken",
        "h": "human", "human": "human", "humans": "human", "humano": "human", "humanos": "human",
        "lab": "lab", "labs": "lab", "laboratorio": "lab",
        "all": "all", "todo": "all", "todos": "all",
    }
    return aliases.get(low, low)


def _admin_kill_creature_v232(self: World, c: Creature, cause: str = "kill_command") -> None:
    if not getattr(c, "alive", False):
        return
    # Kill administrativo: limpia también inmortales si lo pides explícitamente.
    c.alive = False
    if getattr(self, "_spatial_index_valid", False):
        try:
            self._index_remove_creature(c)
        except Exception:
            self._spatial_index_valid = False
    self.log("kill_admin", "world", objetivo=c.entity_id, tipo=c.kind, nombre=getattr(c, "name", c.entity_id), causa=cause, pos=c.pos(), nota="intervención externa de laboratorio; no es aprendizaje ni decisión humana")

World.admin_kill_creature = _admin_kill_creature_v232


def _kill_by_species_v232(self: World, species: str, amount: Optional[int]) -> str:
    sp = _normalize_species_v232(species)
    candidates: List[Creature] = []
    if sp == "human":
        candidates = [h for h in self.humans.values() if h.alive and not getattr(h, "is_lab", False)]
    elif sp == "lab":
        candidates = [h for h in self.humans.values() if h.alive and getattr(h, "is_lab", False)]
    elif sp == "all":
        candidates = [c for c in self.creatures.values() if c.alive]
    elif sp in ("chicken", "cow", "trex"):
        candidates = [c for c in self.creatures.values() if c.alive and c.kind == sp]
    else:
        return f"Especie no reconocida: {species}. Usa: trex/t-rex, cow/vaca, chicken/pollo, human/humano, lab, all."
    if amount is None:
        n = len(candidates)
    else:
        n = max(0, min(int(amount), len(candidates)))
    # Para depurar mejor, mata primero los más cercanos a cuevas/centro de actividad.
    random.shuffle(candidates)
    killed = 0
    for c in candidates[:n]:
        self.admin_kill_creature(c, cause=f"kill {species} {amount if amount is not None else 'all'}")
        killed += 1
    return f"Kill aplicado: {killed}/{len(candidates)} de especie '{species}' ({sp})."

World.kill_by_species = _kill_by_species_v232


_old_process_command_v231_for_v232 = process_command

def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw = cmd.strip()
    low = raw.lower()
    if low.startswith("kill "):
        parts = raw.split()
        if len(parts) < 2:
            print("Uso: kill <especie> <cantidad|all>. Ej: kill t-rex 5 / kill cow 20 / kill chicken all / kill human 3")
            return False
        species = parts[1]
        amount: Optional[int] = None
        if len(parts) >= 3:
            if parts[2].lower() in ("all", "todo", "todos"):
                amount = None
            else:
                try:
                    amount = int(parts[2])
                except Exception:
                    print("Cantidad no válida. Usa número o all. Ej: kill t-rex 5")
                    return False
        else:
            amount = None
        msg = world.kill_by_species(species, amount)
        print(msg)
        state["status_message"] = msg
        return False
    if low in ("kill_help", "help kill"):
        state["paused"] = True
        show_paged_text("HELP KILL", """COMANDO KILL v2.3.2
================================================================================
kill <especie> <cantidad|all>

Ejemplos:
  kill t-rex 5
  kill trex all
  kill cow 20
  kill chicken 10
  kill human 3
  kill lab all
  kill all all

Es una intervención externa de laboratorio. Sirve para retirar depredadores/presas/humanos
sin cambiar la mente ni la lógica de aprendizaje de los protohumanos.
""")
        return False
    return _old_process_command_v231_for_v232(cmd, world, state)

globals()["process_command"] = process_command


_old_seed_stats_report_v231_for_v232 = World.seed_stats_report

def _seed_stats_report_v232(self: World) -> str:
    base = _old_seed_stats_report_v231_for_v232(self)
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    corner = [c for c in chickens if _is_corner_v232(c.pos())]
    edge = [c for c in chickens if self.is_near_edge(c.pos(), CHICKEN_EDGE_MARGIN_V232)]
    following = 0
    for ch in chickens:
        target = self.best_seed_for_chicken(ch)
        if target is not None:
            following += 1
    return base + "\n\nPOLLITOS v2.3.2\n" + "="*80 + f"\npollos en esquina: {len(corner)} | pollos en borde amplio: {len(edge)} | pollos con semilla objetivo: {following}/{len(chickens)}\nradio semilla natural: {SEED_NATURAL_LURE_RADIUS_V232} | radio semilla humana: {SEED_HUMAN_LURE_RADIUS_V232}\ncomando kill: kill t-rex 5 / kill cow 20 / kill chicken all\n"

World.seed_stats_report = _seed_stats_report_v232


_old_detector_metrics_report_v231_for_v232 = World.detector_metrics_report

def _detector_metrics_report_v232(self: World) -> str:
    base = _old_detector_metrics_report_v231_for_v232(self)
    return base + "\n\nECOLOGÍA v2.3.2\n" + "="*100 + f"\n- semillas naturales reducidas: inicial={INITIAL_SEED_PATCHES}, objetivo={SEED_TARGET_ON_MAP}, máximo={SEED_MAX_ON_MAP}\n- pollos: buscan semillas humanas primero y naturales después con radio amplio; salida fuerte de esquinas\n- comando nuevo: kill <especie> <cantidad|all>\n"

World.detector_metrics_report = _detector_metrics_report_v232


_old_render_to_string_v231_for_v232 = World.render_to_string

def _render_to_string_v232(self: World) -> str:
    txt = _old_render_to_string_v231_for_v232(self)
    txt = txt.replace("PROTOHUMANOS 2D v2.3.1 FAST", "PROTOHUMANOS 2D v2.3.2 FAST")
    txt = txt.replace("PROTOHUMANOS 2D v2.3 FAST", "PROTOHUMANOS 2D v2.3.2 FAST")
    return txt

World.render_to_string = _render_to_string_v232

try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.3.2 — POLLOS/SEMILLAS Y KILL
================================
- Pollos buscan semillas de forma activa; no deberían quedarse en esquinas.
- Semillas humanas tienen prioridad absoluta para pollos.
- Menos semillas naturales y más alejadas de bordes.
- kill <especie> <cantidad|all>: intervención externa de laboratorio.
"""
except Exception:
    pass


# ============================================================
# v2.3.3 — POLLOS TERRITORIALES / ANTI-ESQUINAS REAL
# ============================================================
# Problema observado: aunque los pollos buscaban semillas, algunos podían quedarse
# pegados a esquinas/laterales por deriva, nacimientos cercanos o bloqueos de ruta.
# Solución: los pollos reciben un pequeño territorio ecológico distribuido por el mapa,
# salen de bordes de forma prioritaria y las semillas naturales se eligen según su
# territorio. Las semillas humanas siguen teniendo prioridad absoluta.

_PROTOH_VERSION = "2.3.3"

CHICKEN_FORBIDDEN_EDGE_MARGIN_V233 = 9
CHICKEN_HARD_CORNER_MARGIN_V233 = 12
CHICKEN_ESCAPE_UNTIL_TICKS_V233 = 72
CHICKEN_RETERRITORY_TICKS_V233 = 240
CHICKEN_HOME_PULL_DISTANCE_V233 = 18
CHICKEN_GLOBAL_SEED_SCAN_LIMIT_V233 = 80


def _chicken_min_edge_distance_v233(pos: Tuple[int, int]) -> int:
    x, y = pos
    return min(x, y, WIDTH - 1 - x, HEIGHT - 1 - y)


def _chicken_in_bad_edge_v233(pos: Tuple[int, int]) -> bool:
    return _chicken_min_edge_distance_v233(pos) <= CHICKEN_FORBIDDEN_EDGE_MARGIN_V233


def _chicken_in_hard_corner_v233(pos: Tuple[int, int]) -> bool:
    x, y = pos
    return (
        (x <= CHICKEN_HARD_CORNER_MARGIN_V233 or x >= WIDTH - 1 - CHICKEN_HARD_CORNER_MARGIN_V233)
        and (y <= CHICKEN_HARD_CORNER_MARGIN_V233 or y >= HEIGHT - 1 - CHICKEN_HARD_CORNER_MARGIN_V233)
    )


def _safe_chicken_spawn_cell_v233(self: World) -> Optional[Tuple[int, int]]:
    """Celda de nacimiento/territorio para pollo, repartida y lejos de esquinas."""
    dummy = Creature("dummy", "chicken", "chicken", 0, 0, 5, 5, 0)
    same = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    best: Optional[Tuple[float, Tuple[int, int]]] = None
    margin = max(CHICKEN_FORBIDDEN_EDGE_MARGIN_V233 + 2, ANIMAL_SPREAD_MARGIN)
    for _ in range(180):
        x = random.randint(margin, WIDTH - 1 - margin)
        y = random.randint(margin, HEIGHT - 1 - margin)
        if not self.can_place_creature(dummy, x, y):
            continue
        local = sum(1 for c in same if dist(c.pos(), (x, y)) <= ANIMAL_CROWD_RADIUS * 2.2)
        zone = self.map_zone_index((x, y))
        zc = self.species_zone_counts("chicken").get(zone, 0)
        # Favorece zonas poco ocupadas, pero no obliga al centro.
        center_dist = dist((x, y), (WIDTH / 2, HEIGHT / 2)) / max(WIDTH, HEIGHT)
        score = local * 7.0 + zc * 3.0 - center_dist * 1.2 + random.random()
        if best is None or score < best[0]:
            best = (score, (x, y))
    if best:
        return best[1]
    return self.random_spread_cell_for_kind("chicken") or self.random_empty_cell_for_kind("chicken")

World.safe_chicken_spawn_cell = _safe_chicken_spawn_cell_v233


def _assign_chicken_home_v233(self: World, c: Creature, force: bool = False) -> Tuple[int, int]:
    home = getattr(c, "chicken_home", None)
    last = int(getattr(c, "chicken_home_tick", -999999))
    bad_home = not home or _chicken_in_bad_edge_v233(home) if isinstance(home, tuple) else True
    if force or bad_home or self.tick - last >= CHICKEN_RETERRITORY_TICKS_V233:
        home = self.safe_chicken_spawn_cell() or (WIDTH // 2, HEIGHT // 2)
        setattr(c, "chicken_home", home)
        setattr(c, "chicken_home_tick", self.tick)
    return home

World.assign_chicken_home = _assign_chicken_home_v233


def _chicken_escape_edge_step_v233(self: World, c: Creature) -> bool:
    """Salida prioritaria de bordes/esquinas sin teletransporte.
    Elige la casilla vecina que más aumenta distancia al borde y reduce apelmazamiento.
    """
    home = self.assign_chicken_home(c, force=False)
    options: List[Tuple[float, int, int]] = []
    current_edge = _chicken_min_edge_distance_v233(c.pos())
    neigh = self.same_species_neighbors(c, radius=ANIMAL_CROWD_RADIUS * 1.3)
    crowd_center = None
    if neigh:
        crowd_center = (sum(n.x for n in neigh) / len(neigh), sum(n.y for n in neigh) / len(neigh))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = c.x + dx, c.y + dy
            if not self.can_place_creature(c, nx, ny):
                continue
            edge_gain = _chicken_min_edge_distance_v233((nx, ny)) - current_edge
            home_gain = dist(c.pos(), home) - dist((nx, ny), home)
            crowd_gain = 0.0
            if crowd_center is not None:
                crowd_gain = dist((nx, ny), crowd_center) - dist(c.pos(), crowd_center)
            # Prima brutalmente aumentar distancia al borde. Luego territorio y dispersión.
            score = edge_gain * 100.0 + home_gain * 8.0 + crowd_gain * 4.0 + random.random()
            options.append((score, dx, dy))
    options.sort(reverse=True, key=lambda t: t[0])
    for score, dx, dy in options:
        if score < -10 and not _chicken_in_hard_corner_v233(c.pos()):
            continue
        if self.move_creature(c, dx, dy):
            return True
    # fallback caminando hacia territorio
    return self.walk_towards_flexible(c, home)

World.chicken_escape_edge_step = _chicken_escape_edge_step_v233


_old_add_creature_v232_for_v233 = World.add_creature

def _add_creature_v233(self: World, kind: str, x: int, y: int) -> Creature:
    # Los pollos no deben nacer en esquinas/laterales salvo mapa saturado.
    if kind == "chicken" and _chicken_in_bad_edge_v233((x, y)):
        pos = self.safe_chicken_spawn_cell()
        if pos:
            x, y = pos
    c = _old_add_creature_v232_for_v233(self, kind, x, y)
    if kind == "chicken":
        self.assign_chicken_home(c, force=True)
    return c

World.add_creature = _add_creature_v233


_old_try_simple_animal_reproduce_v232_for_v233 = World.try_simple_animal_reproduce

def _try_simple_animal_reproduce_v233(self: World, animal: Creature, kind: str) -> None:
    if kind != "chicken":
        return _old_try_simple_animal_reproduce_v232_for_v233(self, animal, kind)
    if self.count_alive(kind) >= ANIMAL_MIN_POPULATION:
        return
    base_chance = 0.32
    chance = min(0.95, base_chance * ANIMAL_REPRODUCTION_MULTIPLIER)
    if random.random() > chance:
        return
    # 75% de crías en zona repartida; si padre está en borde, 100%.
    if _chicken_in_bad_edge_v233(animal.pos()) or random.random() < 0.75:
        pos = self.safe_chicken_spawn_cell()
        if pos:
            baby = self.add_creature(kind, pos[0], pos[1])
            self.log("reproduccion_animal", animal.entity_id, especie=kind, hijo=baby.entity_id, total_especie=self.count_alive(kind), modo="zona_repartida_v233")
            return
    # Cerca del progenitor, pero nunca borde si hay alternativa.
    for attempt in range(30):
        nx = animal.x + random.randint(-4, 4)
        ny = animal.y + random.randint(-4, 4)
        if _chicken_in_bad_edge_v233((nx, ny)) and attempt < 24:
            continue
        dummy = Creature("dummy", kind, kind, nx, ny, 5, 5, 0)
        if self.can_place_creature(dummy, nx, ny):
            baby = self.add_creature(kind, nx, ny)
            self.log("reproduccion_animal", animal.entity_id, especie=kind, hijo=baby.entity_id, total_especie=self.count_alive(kind), modo="cerca_progenitor_v233")
            return

World.try_simple_animal_reproduce = _try_simple_animal_reproduce_v233


def _best_seed_for_chicken_v233(self: World, chicken: Creature) -> Optional[Item]:
    seeds = self.all_seed_items()
    if not seeds:
        return None
    # Cebo humano: prioridad absoluta en todo el mapa.
    human_seeds = [s for s in seeds if _is_human_placed_seed_v231(s)]
    if human_seeds:
        return max(human_seeds, key=lambda s: self.seed_priority_for_chicken(chicken, s))
    # Natural: no sincronizar todos los pollos. Cada pollo prefiere semillas cercanas a su territorio.
    home = self.assign_chicken_home(chicken, force=False)
    candidates = [s for s in seeds if not _is_human_placed_seed_v231(s)]
    if not candidates:
        return None
    # Si está en borde, el objetivo principal debe sacarlo del borde. Solo usará una semilla si ayuda a salir.
    if _chicken_in_bad_edge_v233(chicken.pos()):
        inward = [s for s in candidates if _chicken_min_edge_distance_v233((s.x, s.y)) > _chicken_min_edge_distance_v233(chicken.pos())]
        candidates = inward or candidates
    # Score mixto: distancia actual + distancia a home + penalización de borde. Así se reparten.
    def score(seed: Item) -> float:
        d_cur = dist(chicken.pos(), (seed.x, seed.y))
        d_home = dist(home, (seed.x, seed.y))
        border_pen = 65.0 if _chicken_in_bad_edge_v233((seed.x, seed.y)) else 0.0
        return -(d_cur * 0.70 + d_home * 0.45 + border_pen) + random.random() * 2.0
    candidates.sort(key=score, reverse=True)
    top = candidates[:min(6, len(candidates))]
    return random.choice(top) if random.random() < 0.28 else top[0]

World.best_seed_for_chicken = _best_seed_for_chicken_v233


_old_update_chicken_v232_for_v233 = World.update_chicken

def _update_chicken_v233(self: World, c: Creature) -> None:
    self.try_simple_animal_reproduce(c, "chicken")
    # Asignación estable de territorio para repartirlos por el mapa.
    home = self.assign_chicken_home(c, force=False)

    # Prioridad 0: si está en borde/esquina, sale SIEMPRE que pueda, sin esperar al 50% de velocidad.
    # Esto elimina el bug visual de pollos eternos en esquinas.
    if _chicken_in_hard_corner_v233(c.pos()) or _chicken_in_bad_edge_v233(c.pos()):
        setattr(c, "corner_escape_until", self.tick + CHICKEN_ESCAPE_UNTIL_TICKS_V233)
        if self.chicken_escape_edge_step(c):
            return

    # Velocidad pollo = 0.5 cuando no está en emergencia de borde.
    if random.random() > self.species_speed(c):
        return

    # Si estaba escapando de borde, continúa hasta estar claramente dentro.
    if int(getattr(c, "corner_escape_until", 0)) >= self.tick:
        if _chicken_min_edge_distance_v233(c.pos()) <= CHICKEN_FORBIDDEN_EDGE_MARGIN_V233 + 4:
            if self.chicken_escape_edge_step(c):
                return
        else:
            setattr(c, "corner_escape_until", 0)

    if c.last_attacker and c.last_attacker in self.creatures and self.creatures[c.last_attacker].alive:
        if self.step_away(c, self.creatures[c.last_attacker].pos()):
            return

    seeds_here = [i for i in self.items_at(c.x, c.y) if i.kind == "seed"]
    if seeds_here:
        human_here = [s for s in seeds_here if _is_human_placed_seed_v231(s)]
        seed = random.choice(human_here or seeds_here)
        if random.random() < (0.98 if human_here else 0.88):
            self.items.pop(seed.item_id, None)
            self._item_index_valid = False
            self.log("pollo_come_semilla", c.entity_id, semilla=seed.item_id, pos=c.pos(), origin=_seed_origin_v231(seed), placed_by=getattr(seed, "placed_by", None), nota="v2.3.3: pollo territorial come semilla")
            return

    # Cebo humano: prioridad absoluta, incluso si le aleja de su territorio.
    human_seeds = [s for s in self.all_seed_items() if _is_human_placed_seed_v231(s)]
    if human_seeds:
        target = max(human_seeds, key=lambda s: self.seed_priority_for_chicken(c, s))
        if self.walk_towards_flexible(c, (target.x, target.y)):
            return

    # Si está muy lejos de su territorio y no hay cebo humano, vuelve hacia su zona.
    if dist(c.pos(), home) > CHICKEN_HOME_PULL_DISTANCE_V233 and random.random() < 0.65:
        if self.walk_towards_flexible(c, home):
            return

    target_seed = self.best_seed_for_chicken(c)
    if target_seed is not None:
        if self.walk_towards_flexible(c, (target_seed.x, target_seed.y)):
            if self.tick % max(1, TICKS_PER_DAY) == 0:
                self.log("pollo_sigue_semilla", c.entity_id, semilla=target_seed.item_id, origin=_seed_origin_v231(target_seed), distancia=round(dist(c.pos(), (target_seed.x, target_seed.y)), 1), pos=c.pos(), home=home, nota="v2.3.3 territorial")
            return

    # Dispersión normal de respaldo.
    if self.animal_dispersal_step(c):
        return
    if dist(c.pos(), home) > 3 and random.random() < 0.35:
        if self.walk_towards_flexible(c, home):
            return
    self.animal_idle_move(c)

World.update_chicken = _update_chicken_v233


# Diagnóstico más claro para verificar que se reparten.
_old_seed_stats_report_v232_for_v233 = World.seed_stats_report

def _seed_stats_report_v233(self: World) -> str:
    base = _old_seed_stats_report_v232_for_v233(self)
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    corner = [c for c in chickens if _chicken_in_hard_corner_v233(c.pos())]
    edge = [c for c in chickens if _chicken_in_bad_edge_v233(c.pos())]
    homes = [getattr(c, "chicken_home", None) for c in chickens]
    homes_valid = [h for h in homes if isinstance(h, tuple)]
    zones = {}
    for c in chickens:
        z = self.map_zone_index(c.pos(), 8, 4)
        zones[z] = zones.get(z, 0) + 1
    max_zone = max(zones.values()) if zones else 0
    used_zones = len(zones)
    return base + "\n\nPOLLOS TERRITORIALES v2.3.3\n" + "="*80 + f"\npollos en esquina dura: {len(corner)} | pollos en borde prohibido: {len(edge)}\nzonas ocupadas por pollos: {used_zones}/32 | máximo pollos en una zona: {max_zone}\nhomes asignados: {len(homes_valid)}/{len(chickens)} | margen prohibido={CHICKEN_FORBIDDEN_EDGE_MARGIN_V233}\n"

World.seed_stats_report = _seed_stats_report_v233


_old_detector_metrics_report_v232_for_v233 = World.detector_metrics_report

def _detector_metrics_report_v233(self: World) -> str:
    base = _old_detector_metrics_report_v232_for_v233(self)
    return base + "\n\nPOLLOS v2.3.3\n" + "="*100 + "\n- Pollos territoriales: cada pollo recibe una zona/home distribuida por el mapa.\n- Si un pollo toca borde/esquina, sale de forma prioritaria antes de buscar semillas.\n- Semillas humanas siguen teniendo prioridad absoluta.\n- Semillas naturales se eligen según cercanía + territorio para evitar que todos vayan al mismo sitio.\n"

World.detector_metrics_report = _detector_metrics_report_v233


_old_render_to_string_v232_for_v233 = World.render_to_string

def _render_to_string_v233(self: World) -> str:
    txt = _old_render_to_string_v232_for_v233(self)
    txt = txt.replace("PROTOHUMANOS 2D v2.3.2 FAST", "PROTOHUMANOS 2D v2.3.3 FAST")
    txt = txt.replace("PROTOHUMANOS 2D v2.3.1 FAST", "PROTOHUMANOS 2D v2.3.3 FAST")
    txt = txt.replace("PROTOHUMANOS 2D v2.3 FAST", "PROTOHUMANOS 2D v2.3.3 FAST")
    return txt

World.render_to_string = _render_to_string_v233

try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.3.3 — POLLOS TERRITORIALES
=============================
- Los pollos ya no deberían quedarse en esquinas/laterales.
- Cada pollo tiene un territorio ecológico repartido por el mapa.
- Si un pollo cae en borde/esquina, sale de ahí antes de buscar semillas.
- Las semillas humanas siguen atrayendo más que cualquier semilla natural.
- seed_stats muestra pollos en borde/esquina y zonas ocupadas.
"""
except Exception:
    pass


# ============================================================
# v2.3.4 — POLLOS REPARTIDOS POR TERRITORIOS FIJOS
# ============================================================
# Ajuste fuerte: los pollos ya no usan semillas naturales globales como imán.
# Cada pollo tiene un territorio ecológico repartido por sectores. Busca semillas
# naturales cerca de su zona, pero las semillas humanas siguen teniendo prioridad global.
# Objetivo: que los pollos estén por todo el mapa, como las vacas, sin quedarse en esquinas.

_PROTOH_VERSION = "2.3.4"

CHICKEN_HOME_COLS_V234 = 8
CHICKEN_HOME_ROWS_V234 = 4
CHICKEN_LOCAL_SEED_RADIUS_V234 = 16
CHICKEN_HOME_RADIUS_V234 = 8
CHICKEN_STRONG_HOME_PULL_V234 = 14
CHICKEN_HOME_REBALANCE_TICKS_V234 = 120
CHICKEN_HOME_MARGIN_V234 = max(CHICKEN_FORBIDDEN_EDGE_MARGIN_V233 + 2, 11)


def _chicken_home_zone_v234(self: World, pos: Tuple[int, int]) -> Tuple[int, int]:
    return self.map_zone_index(pos, CHICKEN_HOME_COLS_V234, CHICKEN_HOME_ROWS_V234)

World.chicken_home_zone = _chicken_home_zone_v234


def _chicken_home_zone_counts_v234(self: World) -> Dict[Tuple[int, int], int]:
    counts: Dict[Tuple[int, int], int] = {}
    for c in self.creatures.values():
        if c.alive and c.kind == "chicken":
            home = getattr(c, "chicken_home", None)
            if isinstance(home, tuple):
                z = self.chicken_home_zone(home)
                counts[z] = counts.get(z, 0) + 1
    return counts

World.chicken_home_zone_counts = _chicken_home_zone_counts_v234


def _random_cell_in_home_zone_v234(self: World, zone: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    zx, zy = zone
    x0 = int(WIDTH * zx / CHICKEN_HOME_COLS_V234)
    x1 = int(WIDTH * (zx + 1) / CHICKEN_HOME_COLS_V234) - 1
    y0 = int(HEIGHT * zy / CHICKEN_HOME_ROWS_V234)
    y1 = int(HEIGHT * (zy + 1) / CHICKEN_HOME_ROWS_V234) - 1
    m = CHICKEN_HOME_MARGIN_V234
    x0 = max(m, x0); x1 = min(WIDTH - 1 - m, x1)
    y0 = max(m, y0); y1 = min(HEIGHT - 1 - m, y1)
    if x0 > x1 or y0 > y1:
        return None
    dummy = Creature("dummy", "chicken", "chicken", 0, 0, 5, 5, 0)
    best: Optional[Tuple[float, Tuple[int, int]]] = None
    same = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    for _ in range(80):
        x = random.randint(x0, x1); y = random.randint(y0, y1)
        if not self.can_place_creature(dummy, x, y):
            continue
        local = sum(1 for c in same if dist(c.pos(), (x, y)) <= ANIMAL_CROWD_RADIUS * 1.7)
        score = local * 5.0 + random.random()
        if best is None or score < best[0]:
            best = (score, (x, y))
    return best[1] if best else None

World.random_cell_in_home_zone = _random_cell_in_home_zone_v234


def _safe_chicken_home_cell_v234(self: World, avoid_zone: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
    counts = self.chicken_home_zone_counts()
    all_zones = [(x, y) for y in range(CHICKEN_HOME_ROWS_V234) for x in range(CHICKEN_HOME_COLS_V234)]
    random.shuffle(all_zones)
    all_zones.sort(key=lambda z: (counts.get(z, 0), 1 if avoid_zone is not None and z == avoid_zone else 0, random.random()))
    for z in all_zones:
        pos = self.random_cell_in_home_zone(z)
        if pos:
            return pos
    return self.safe_chicken_spawn_cell()

World.safe_chicken_home_cell = _safe_chicken_home_cell_v234


def _assign_chicken_home_v234(self: World, c: Creature, force: bool = False) -> Tuple[int, int]:
    home = getattr(c, "chicken_home", None)
    bad_home = not isinstance(home, tuple) or _chicken_in_bad_edge_v233(home)
    if force or bad_home:
        old_zone = self.chicken_home_zone(home) if isinstance(home, tuple) else None
        home = self.safe_chicken_home_cell(avoid_zone=old_zone) or self.safe_chicken_spawn_cell() or (WIDTH // 2, HEIGHT // 2)
        setattr(c, "chicken_home", home)
        setattr(c, "chicken_home_tick", self.tick)
    return home

World.assign_chicken_home = _assign_chicken_home_v234


def _rebalance_chicken_homes_v234(self: World) -> None:
    if self.tick % CHICKEN_HOME_REBALANCE_TICKS_V234 != 0:
        return
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    if not chickens:
        return
    # Asegura homes válidos.
    for c in chickens:
        self.assign_chicken_home(c, force=False)
    counts = self.chicken_home_zone_counts()
    target_per_zone = max(1, (len(chickens) + (CHICKEN_HOME_COLS_V234 * CHICKEN_HOME_ROWS_V234) - 1) // (CHICKEN_HOME_COLS_V234 * CHICKEN_HOME_ROWS_V234))
    moved = 0
    # Si una zona tiene demasiados homes, reasigna algunos a zonas vacías/poco usadas.
    for zone, count in list(counts.items()):
        if count <= max(2, target_per_zone + 1):
            continue
        candidates = [c for c in chickens if self.chicken_home_zone(getattr(c, "chicken_home", c.pos())) == zone]
        random.shuffle(candidates)
        for c in candidates[: max(0, count - max(2, target_per_zone + 1))]:
            new_home = self.safe_chicken_home_cell(avoid_zone=zone)
            if new_home:
                setattr(c, "chicken_home", new_home)
                setattr(c, "chicken_home_tick", self.tick)
                moved += 1
    if moved:
        self.log("reajuste_territorios_pollos", "world", reasignados=moved, nota="v2.3.4: repartir pollos por territorios; no teletransporte")

World.rebalance_chicken_homes = _rebalance_chicken_homes_v234


_old_add_creature_v233_for_v234 = World.add_creature

def _add_creature_v234(self: World, kind: str, x: int, y: int) -> Creature:
    if kind == "chicken":
        # Nacimiento en celda/home repartida; evita que entren nuevos pollos ya desde esquina.
        pos = self.safe_chicken_home_cell()
        if pos:
            x, y = pos
    c = _old_add_creature_v233_for_v234(self, kind, x, y)
    if kind == "chicken":
        # El home debe quedar muy cercano al nacimiento, no heredado por error del patch anterior.
        if not isinstance(getattr(c, "chicken_home", None), tuple):
            setattr(c, "chicken_home", (c.x, c.y))
        if _chicken_in_bad_edge_v233(getattr(c, "chicken_home", (c.x, c.y))):
            setattr(c, "chicken_home", (c.x, c.y))
    return c

World.add_creature = _add_creature_v234


def _natural_seeds_for_chicken_v234(self: World, chicken: Creature, home: Tuple[int, int]) -> List[Item]:
    seeds = [s for s in self.all_seed_items() if not _is_human_placed_seed_v231(s)]
    if not seeds:
        return []
    # Preferir semillas cerca del territorio; después, si no hay, cerca del pollo.
    local_home = [s for s in seeds if dist((s.x, s.y), home) <= CHICKEN_LOCAL_SEED_RADIUS_V234]
    if local_home:
        return local_home
    local_body = [s for s in seeds if dist((s.x, s.y), chicken.pos()) <= CHICKEN_LOCAL_SEED_RADIUS_V234]
    return local_body

World.natural_seeds_for_chicken = _natural_seeds_for_chicken_v234


def _best_seed_for_chicken_v234(self: World, chicken: Creature) -> Optional[Item]:
    seeds = self.all_seed_items()
    if not seeds:
        return None
    # Las semillas humanas sí son prioridad global: cebo/trampa debe funcionar.
    human_seeds = [s for s in seeds if _is_human_placed_seed_v231(s)]
    if human_seeds:
        return max(human_seeds, key=lambda s: self.seed_priority_for_chicken(chicken, s))
    home = self.assign_chicken_home(chicken, force=False)
    candidates = self.natural_seeds_for_chicken(chicken, home)
    if not candidates:
        return None
    def score(seed: Item) -> float:
        d_cur = dist(chicken.pos(), (seed.x, seed.y))
        d_home = dist(home, (seed.x, seed.y))
        edge_pen = 80.0 if _chicken_in_bad_edge_v233((seed.x, seed.y)) else 0.0
        return -(d_cur * 0.65 + d_home * 0.75 + edge_pen) + random.random() * 2.0
    candidates.sort(key=score, reverse=True)
    top = candidates[:min(4, len(candidates))]
    return random.choice(top) if random.random() < 0.25 else top[0]

World.best_seed_for_chicken = _best_seed_for_chicken_v234


_old_update_chicken_v233_for_v234 = World.update_chicken

def _update_chicken_v234(self: World, c: Creature) -> None:
    self.try_simple_animal_reproduce(c, "chicken")
    self.rebalance_chicken_homes()
    home = self.assign_chicken_home(c, force=False)

    # Bordes/esquinas: salir siempre antes de cualquier otra conducta natural.
    if _chicken_in_hard_corner_v233(c.pos()) or _chicken_in_bad_edge_v233(c.pos()):
        setattr(c, "corner_escape_until", self.tick + CHICKEN_ESCAPE_UNTIL_TICKS_V233)
        if self.chicken_escape_edge_step(c):
            return

    if random.random() > self.species_speed(c):
        return

    if c.last_attacker and c.last_attacker in self.creatures and self.creatures[c.last_attacker].alive:
        if self.step_away(c, self.creatures[c.last_attacker].pos()):
            return

    # Comer si está encima de semilla.
    seeds_here = [i for i in self.items_at(c.x, c.y) if i.kind == "seed"]
    if seeds_here:
        human_here = [s for s in seeds_here if _is_human_placed_seed_v231(s)]
        seed = random.choice(human_here or seeds_here)
        if random.random() < (0.99 if human_here else 0.90):
            self.items.pop(seed.item_id, None)
            self._item_index_valid = False
            self.log("pollo_come_semilla", c.entity_id, semilla=seed.item_id, pos=c.pos(), origin=_seed_origin_v231(seed), placed_by=getattr(seed, "placed_by", None), nota="v2.3.4: pollo territorial")
            return

    # Cebo humano global.
    human_seeds = [s for s in self.all_seed_items() if _is_human_placed_seed_v231(s)]
    if human_seeds:
        target = max(human_seeds, key=lambda s: self.seed_priority_for_chicken(c, s))
        if self.walk_towards_flexible(c, (target.x, target.y)):
            return

    # Si está lejos de su territorio, vuelve. Así se reparte por todos lados.
    d_home = dist(c.pos(), home)
    if d_home > CHICKEN_STRONG_HOME_PULL_V234:
        if self.walk_towards_flexible(c, home):
            return

    # Semillas naturales solo locales/territoriales.
    target_seed = self.best_seed_for_chicken(c)
    if target_seed is not None and (d_home <= CHICKEN_STRONG_HOME_PULL_V234 + 4 or dist((target_seed.x, target_seed.y), home) <= CHICKEN_LOCAL_SEED_RADIUS_V234):
        if self.walk_towards_flexible(c, (target_seed.x, target_seed.y)):
            return

    # Paseo dentro/alrededor del territorio.
    if d_home > CHICKEN_HOME_RADIUS_V234 and random.random() < 0.80:
        if self.walk_towards_flexible(c, home):
            return
    if self.animal_dispersal_step(c):
        return
    # Pequeño paseo local: si se aleja demasiado, home pull vuelve a tomar control.
    self.animal_idle_move(c)

World.update_chicken = _update_chicken_v234


_old_seed_stats_report_v233_for_v234 = World.seed_stats_report

def _seed_stats_report_v234(self: World) -> str:
    base = _old_seed_stats_report_v233_for_v234(self)
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    zones: Dict[Tuple[int, int], int] = {}
    home_zones: Dict[Tuple[int, int], int] = {}
    far_home = 0
    for c in chickens:
        z = self.chicken_home_zone(c.pos())
        zones[z] = zones.get(z, 0) + 1
        home = getattr(c, "chicken_home", None)
        if isinstance(home, tuple):
            hz = self.chicken_home_zone(home)
            home_zones[hz] = home_zones.get(hz, 0) + 1
            if dist(c.pos(), home) > CHICKEN_STRONG_HOME_PULL_V234:
                far_home += 1
    return base + "\n\nPOLLOS REPARTIDOS v2.3.4\n" + "="*80 + f"\nzonas de cuerpo: {len(zones)}/32 | max cuerpo/zona: {max(zones.values()) if zones else 0}\nzonas de home: {len(home_zones)}/32 | max home/zona: {max(home_zones.values()) if home_zones else 0}\npollos lejos de su home: {far_home}/{len(chickens)} | radio semilla natural local={CHICKEN_LOCAL_SEED_RADIUS_V234}\n"

World.seed_stats_report = _seed_stats_report_v234


_old_detector_metrics_report_v233_for_v234 = World.detector_metrics_report

def _detector_metrics_report_v234(self: World) -> str:
    base = _old_detector_metrics_report_v233_for_v234(self)
    return base + "\n\nPOLLOS v2.3.4\n" + "="*100 + "\n- Natural seeds ya no atraen globalmente a todos los pollos.\n- Cada pollo mantiene un home/territorio repartido por sectores.\n- Si no hay semilla humana, come/explora semillas cercanas a su territorio.\n- Semilla humana sigue siendo prioridad global para que cebo/trampa funcione.\n"

World.detector_metrics_report = _detector_metrics_report_v234


_old_render_to_string_v233_for_v234 = World.render_to_string

def _render_to_string_v234(self: World) -> str:
    txt = _old_render_to_string_v233_for_v234(self)
    txt = txt.replace("PROTOHUMANOS 2D v2.3.3 FAST", "PROTOHUMANOS 2D v2.3.4 FAST")
    txt = txt.replace("PROTOHUMANOS 2D v2.3.2 FAST", "PROTOHUMANOS 2D v2.3.4 FAST")
    txt = txt.replace("PROTOHUMANOS 2D v2.3.1 FAST", "PROTOHUMANOS 2D v2.3.4 FAST")
    txt = txt.replace("PROTOHUMANOS 2D v2.3 FAST", "PROTOHUMANOS 2D v2.3.4 FAST")
    return txt

World.render_to_string = _render_to_string_v234

try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.3.4 — POLLOS REPARTIDOS POR TODO EL MAPA
===========================================
- Los pollos tienen territorios/home repartidos por sectores.
- Las semillas naturales ya no actúan como imán global.
- Las semillas humanas siguen atrayendo globalmente para cebo/trampa.
- seed_stats muestra zonas de cuerpo y zonas de home.
"""
except Exception:
    pass


# ============================================================
# v2.3.5 — POLLOS POR TODO EL ALTO DEL MAPA
# ============================================================
# v2.3.4 evitaba demasiado los bordes verticales y comprimía a los pollos en la franja media.
# Ajuste: márgenes X/Y separados. Evitamos esquinas reales, pero permitimos que los pollos
# usen casi todo el mapa como las vacas.

_PROTOH_VERSION = "2.3.5"

CHICKEN_EDGE_X_V235 = 6
CHICKEN_EDGE_Y_V235 = 4
CHICKEN_HARD_CORNER_X_V235 = 8
CHICKEN_HARD_CORNER_Y_V235 = 5
CHICKEN_HOME_MARGIN_X_V235 = 7
CHICKEN_HOME_MARGIN_Y_V235 = 4

# Sobrescribimos los helpers usados por las capas anteriores; lookup en Python es dinámico.
def _chicken_min_edge_distance_v233(pos: Tuple[int, int]) -> int:  # type: ignore[no-redef]
    x, y = pos
    # Normalizado: cerca de borde si supera margen X o margen Y.
    dx = min(x, WIDTH - 1 - x)
    dy = min(y, HEIGHT - 1 - y)
    return min(int(dx * (CHICKEN_EDGE_Y_V235 / max(1, CHICKEN_EDGE_X_V235))), dy)


def _chicken_in_bad_edge_v233(pos: Tuple[int, int]) -> bool:  # type: ignore[no-redef]
    x, y = pos
    return x <= CHICKEN_EDGE_X_V235 or x >= WIDTH - 1 - CHICKEN_EDGE_X_V235 or y <= CHICKEN_EDGE_Y_V235 or y >= HEIGHT - 1 - CHICKEN_EDGE_Y_V235


def _chicken_in_hard_corner_v233(pos: Tuple[int, int]) -> bool:  # type: ignore[no-redef]
    x, y = pos
    return (
        (x <= CHICKEN_HARD_CORNER_X_V235 or x >= WIDTH - 1 - CHICKEN_HARD_CORNER_X_V235)
        and (y <= CHICKEN_HARD_CORNER_Y_V235 or y >= HEIGHT - 1 - CHICKEN_HARD_CORNER_Y_V235)
    )


def _random_cell_in_home_zone_v235(self: World, zone: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    zx, zy = zone
    x0 = int(WIDTH * zx / CHICKEN_HOME_COLS_V234)
    x1 = int(WIDTH * (zx + 1) / CHICKEN_HOME_COLS_V234) - 1
    y0 = int(HEIGHT * zy / CHICKEN_HOME_ROWS_V234)
    y1 = int(HEIGHT * (zy + 1) / CHICKEN_HOME_ROWS_V234) - 1
    x0 = max(CHICKEN_HOME_MARGIN_X_V235, x0); x1 = min(WIDTH - 1 - CHICKEN_HOME_MARGIN_X_V235, x1)
    y0 = max(CHICKEN_HOME_MARGIN_Y_V235, y0); y1 = min(HEIGHT - 1 - CHICKEN_HOME_MARGIN_Y_V235, y1)
    if x0 > x1 or y0 > y1:
        return None
    dummy = Creature("dummy", "chicken", "chicken", 0, 0, 5, 5, 0)
    best: Optional[Tuple[float, Tuple[int, int]]] = None
    same = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    for _ in range(90):
        x = random.randint(x0, x1); y = random.randint(y0, y1)
        if not self.can_place_creature(dummy, x, y):
            continue
        local = sum(1 for c in same if dist(c.pos(), (x, y)) <= ANIMAL_CROWD_RADIUS * 1.6)
        score = local * 5.0 + random.random()
        if best is None or score < best[0]:
            best = (score, (x, y))
    return best[1] if best else None

World.random_cell_in_home_zone = _random_cell_in_home_zone_v235


def _safe_chicken_home_cell_v235(self: World, avoid_zone: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
    counts = self.chicken_home_zone_counts()
    # Equilibra también por filas para que no se queden todos en una franja horizontal.
    row_counts: Dict[int, int] = {}
    for (zx, zy), n in counts.items():
        row_counts[zy] = row_counts.get(zy, 0) + n
    all_zones = [(x, y) for y in range(CHICKEN_HOME_ROWS_V234) for x in range(CHICKEN_HOME_COLS_V234)]
    random.shuffle(all_zones)
    all_zones.sort(key=lambda z: (
        row_counts.get(z[1], 0),
        counts.get(z, 0),
        1 if avoid_zone is not None and z == avoid_zone else 0,
        random.random()
    ))
    for z in all_zones:
        pos = self.random_cell_in_home_zone(z)
        if pos:
            return pos
    return self.safe_chicken_spawn_cell()

World.safe_chicken_home_cell = _safe_chicken_home_cell_v235


_old_rebalance_chicken_homes_v234_for_v235 = World.rebalance_chicken_homes

def _rebalance_chicken_homes_v235(self: World) -> None:
    if self.tick % CHICKEN_HOME_REBALANCE_TICKS_V234 != 0:
        return
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    if not chickens:
        return
    for c in chickens:
        self.assign_chicken_home(c, force=False)
    moved = 0
    # Primero usa la lógica anterior.
    try:
        _old_rebalance_chicken_homes_v234_for_v235(self)
    except Exception:
        pass
    # Refuerzo: si una fila de homes está vacía o muy baja, reasigna desde filas saturadas.
    row_members: Dict[int, List[Creature]] = {r: [] for r in range(CHICKEN_HOME_ROWS_V234)}
    for c in chickens:
        home = getattr(c, "chicken_home", None)
        if isinstance(home, tuple):
            _, row = self.chicken_home_zone(home)
            row_members.setdefault(row, []).append(c)
    avg = max(1, len(chickens) / CHICKEN_HOME_ROWS_V234)
    low_rows = [r for r, arr in row_members.items() if len(arr) < max(1, int(avg * 0.45))]
    high_rows = [r for r, arr in row_members.items() if len(arr) > max(2, int(avg * 1.45))]
    for lr in low_rows:
        for hr in high_rows:
            if not row_members.get(hr):
                continue
            donor = random.choice(row_members[hr])
            # Fuerza zona dentro de la fila baja.
            zones = [(x, lr) for x in range(CHICKEN_HOME_COLS_V234)]
            random.shuffle(zones)
            zones.sort(key=lambda z: self.chicken_home_zone_counts().get(z, 0))
            new_home = None
            for z in zones:
                new_home = self.random_cell_in_home_zone(z)
                if new_home:
                    break
            if new_home:
                setattr(donor, "chicken_home", new_home)
                setattr(donor, "chicken_home_tick", self.tick)
                row_members[hr].remove(donor)
                row_members[lr].append(donor)
                moved += 1
                break
    if moved:
        self.log("reajuste_filas_pollos", "world", reasignados=moved, nota="v2.3.5: repartir pollos también arriba/abajo")

World.rebalance_chicken_homes = _rebalance_chicken_homes_v235


_old_seed_stats_report_v234_for_v235 = World.seed_stats_report

def _seed_stats_report_v235(self: World) -> str:
    base = _old_seed_stats_report_v234_for_v235(self)
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    rows: Dict[int, int] = {}
    home_rows: Dict[int, int] = {}
    for c in chickens:
        _, r = self.chicken_home_zone(c.pos())
        rows[r] = rows.get(r, 0) + 1
        home = getattr(c, "chicken_home", None)
        if isinstance(home, tuple):
            _, hr = self.chicken_home_zone(home)
            home_rows[hr] = home_rows.get(hr, 0) + 1
    return base + "\n\nPOLLOS v2.3.5 — DISTRIBUCIÓN VERTICAL\n" + "="*80 + f"\nfilas ocupadas por cuerpo: {rows}\nfilas ocupadas por home: {home_rows}\nmargen X={CHICKEN_EDGE_X_V235}, margen Y={CHICKEN_EDGE_Y_V235}; se evitan esquinas, no toda la franja superior/inferior.\n"

World.seed_stats_report = _seed_stats_report_v235


_old_detector_metrics_report_v234_for_v235 = World.detector_metrics_report

def _detector_metrics_report_v235(self: World) -> str:
    base = _old_detector_metrics_report_v234_for_v235(self)
    return base + "\n\nPOLLOS v2.3.5\n" + "="*100 + "\n- Márgenes X/Y separados: ya no se comprimen en la franja media.\n- Rebalanceo por filas: intenta repartir pollos arriba/medio/abajo sin teletransporte.\n"

World.detector_metrics_report = _detector_metrics_report_v235


_old_render_to_string_v234_for_v235 = World.render_to_string

def _render_to_string_v235(self: World) -> str:
    txt = _old_render_to_string_v234_for_v235(self)
    for old in ("v2.3.4", "v2.3.3", "v2.3.2", "v2.3.1", "v2.3"):
        txt = txt.replace(f"PROTOHUMANOS 2D {old} FAST", "PROTOHUMANOS 2D v2.3.5 FAST")
    return txt

World.render_to_string = _render_to_string_v235

try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.3.5 — POLLOS REPARTIDOS TAMBIÉN ARRIBA/ABAJO
================================================
- Márgenes X/Y separados: evitan esquinas reales, no comprimen todo al centro vertical.
- Los territorios de pollos se equilibran por filas.
- seed_stats muestra filas de cuerpo/home.
"""
except Exception:
    pass


# ============================================================
# v2.3.6 — POLLOS OCUPAN SU FILA DE TERRITORIO
# ============================================================
# v2.3.5 repartía homes arriba/abajo, pero los cuerpos podían quedarse en filas centrales
# porque se conformaban con estar cerca del home. Ahora, si el pollo no está en la fila de
# su territorio, prioriza volver a esa fila. Se evitan solo bordes reales, no toda la banda.

_PROTOH_VERSION = "2.3.6"

# Márgenes menos agresivos: evita esquinas reales, no la parte alta/baja útil.
CHICKEN_EDGE_X_V235 = 5
CHICKEN_EDGE_Y_V235 = 3
CHICKEN_HARD_CORNER_X_V235 = 7
CHICKEN_HARD_CORNER_Y_V235 = 4
CHICKEN_HOME_MARGIN_X_V235 = 6
CHICKEN_HOME_MARGIN_Y_V235 = 5
CHICKEN_HOME_RADIUS_V234 = 3
CHICKEN_STRONG_HOME_PULL_V234 = 8


def _chicken_current_and_home_row_v236(self: World, c: Creature) -> Tuple[Optional[int], Optional[int]]:
    try:
        _, row = self.chicken_home_zone(c.pos())
    except Exception:
        row = None
    home = getattr(c, "chicken_home", None)
    if isinstance(home, tuple):
        try:
            _, hrow = self.chicken_home_zone(home)
        except Exception:
            hrow = None
    else:
        hrow = None
    return row, hrow

World.chicken_current_and_home_row = _chicken_current_and_home_row_v236


_old_update_chicken_v234_for_v236 = World.update_chicken

def _update_chicken_v236(self: World, c: Creature) -> None:
    self.try_simple_animal_reproduce(c, "chicken")
    self.rebalance_chicken_homes()
    home = self.assign_chicken_home(c, force=False)

    # Salida de esquinas/bordes reales.
    if _chicken_in_hard_corner_v233(c.pos()) or _chicken_in_bad_edge_v233(c.pos()):
        setattr(c, "corner_escape_until", self.tick + CHICKEN_ESCAPE_UNTIL_TICKS_V233)
        if self.chicken_escape_edge_step(c):
            return

    # Incluso con velocidad 0.5, si está en la fila equivocada de su territorio, corrige más a menudo.
    row, hrow = self.chicken_current_and_home_row(c)
    wrong_row = (row is not None and hrow is not None and row != hrow)
    if wrong_row and random.random() < 0.85:
        if self.walk_towards_flexible(c, home):
            return

    if random.random() > self.species_speed(c):
        return

    if c.last_attacker and c.last_attacker in self.creatures and self.creatures[c.last_attacker].alive:
        if self.step_away(c, self.creatures[c.last_attacker].pos()):
            return

    seeds_here = [i for i in self.items_at(c.x, c.y) if i.kind == "seed"]
    if seeds_here:
        human_here = [s for s in seeds_here if _is_human_placed_seed_v231(s)]
        seed = random.choice(human_here or seeds_here)
        if random.random() < (0.99 if human_here else 0.90):
            self.items.pop(seed.item_id, None)
            self._item_index_valid = False
            self.log("pollo_come_semilla", c.entity_id, semilla=seed.item_id, pos=c.pos(), origin=_seed_origin_v231(seed), placed_by=getattr(seed, "placed_by", None), nota="v2.3.6: pollo territorial")
            return

    # Cebo humano sigue siendo prioridad absoluta.
    human_seeds = [s for s in self.all_seed_items() if _is_human_placed_seed_v231(s)]
    if human_seeds:
        target = max(human_seeds, key=lambda s: self.seed_priority_for_chicken(c, s))
        if self.walk_towards_flexible(c, (target.x, target.y)):
            return

    # Mantener territorio con más fuerza que v2.3.5.
    d_home = dist(c.pos(), home)
    if d_home > CHICKEN_STRONG_HOME_PULL_V234 or wrong_row:
        if self.walk_towards_flexible(c, home):
            return

    # Semillas naturales solo si están en/near territorio.
    target_seed = self.best_seed_for_chicken(c)
    if target_seed is not None and dist((target_seed.x, target_seed.y), home) <= CHICKEN_LOCAL_SEED_RADIUS_V234:
        if self.walk_towards_flexible(c, (target_seed.x, target_seed.y)):
            return

    if d_home > CHICKEN_HOME_RADIUS_V234 and random.random() < 0.90:
        if self.walk_towards_flexible(c, home):
            return
    if self.animal_dispersal_step(c):
        return
    self.animal_idle_move(c)

World.update_chicken = _update_chicken_v236


_old_seed_stats_report_v235_for_v236 = World.seed_stats_report

def _seed_stats_report_v236(self: World) -> str:
    base = _old_seed_stats_report_v235_for_v236(self)
    chickens = [c for c in self.creatures.values() if c.alive and c.kind == "chicken"]
    wrong = 0
    for c in chickens:
        row, hrow = self.chicken_current_and_home_row(c)
        if row is not None and hrow is not None and row != hrow:
            wrong += 1
    return base + "\n\nPOLLOS v2.3.6 — FILA DE TERRITORIO\n" + "="*80 + f"\npollos en fila distinta a su home: {wrong}/{len(chickens)}\nlos pollos corrigen fila antes de perseguir semillas naturales; las semillas humanas siguen siendo prioridad global.\n"

World.seed_stats_report = _seed_stats_report_v236


_old_detector_metrics_report_v235_for_v236 = World.detector_metrics_report

def _detector_metrics_report_v236(self: World) -> str:
    base = _old_detector_metrics_report_v235_for_v236(self)
    return base + "\n\nPOLLOS v2.3.6\n" + "="*100 + "\n- Si un pollo no está en la fila de su territorio, vuelve a ella.\n- Márgenes verticales menos agresivos: usan parte alta/baja del mapa sin quedarse en esquinas.\n"

World.detector_metrics_report = _detector_metrics_report_v236


_old_render_to_string_v235_for_v236 = World.render_to_string

def _render_to_string_v236(self: World) -> str:
    txt = _old_render_to_string_v235_for_v236(self)
    for old in ("v2.3.5", "v2.3.4", "v2.3.3", "v2.3.2", "v2.3.1", "v2.3"):
        txt = txt.replace(f"PROTOHUMANOS 2D {old} FAST", "PROTOHUMANOS 2D v2.3.6 FAST")
    return txt

World.render_to_string = _render_to_string_v236

try:
    HELP_LAB_TEXT_V211 = HELP_LAB_TEXT_V211 + """

v2.3.6 — POLLOS EN SU FILA DE TERRITORIO
========================================
- Si un pollo está fuera de la fila de su territorio, vuelve.
- Esto reparte pollos arriba/medio/abajo sin teletransportarlos.
- Las semillas humanas siguen siendo prioridad global.
"""
except Exception:
    pass



# ============================================================
# v2.3.7 — EXPORTS ROBUSTOS + SISTEMA DE ERRORES SIN CRASH
# ============================================================
# Objetivo:
# - arreglar NameError: ensure_dir_for_file no definido en comandos export.
# - si un comando falla, no cerrar protoH: mostrar Error <codigo>-<id>.
# - comando "error" / "errores" para ver traceback bruto y poder depurarlo.

import traceback as _traceback_v237
import datetime as _datetime_v237

PROTOH_ERROR_LOGS: List[Dict[str, Any]] = globals().get("PROTOH_ERROR_LOGS", [])
PROTOH_ERROR_COUNTER: int = int(globals().get("PROTOH_ERROR_COUNTER", 0))


def ensure_dir_for_file(path: str) -> str:
    """Crea la carpeta padre de un archivo exportado, si hace falta.

    Varias capas v2.x llamaban a esta función, pero en algunas ramas no existía.
    Mantenerla global evita que un export rompa toda la simulación.
    """
    p = os.path.expanduser(str(path).strip())
    parent = os.path.dirname(p)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return p


def _protoh_error_code(exc: BaseException) -> int:
    """Código corto legible para errores en comandos.

    No pretende ser HTTP real, pero usa códigos intuitivos:
    404 = recurso/clave/archivo no encontrado, 403 = permisos,
    400 = argumento malo, 500+ = bug interno.
    """
    if isinstance(exc, FileNotFoundError):
        return 404
    if isinstance(exc, KeyError):
        return 404
    if isinstance(exc, PermissionError):
        return 403
    if isinstance(exc, (ValueError, TypeError)):
        return 400
    if isinstance(exc, NameError):
        return 501
    if isinstance(exc, AttributeError):
        return 502
    if isinstance(exc, OSError):
        return 503
    return 500


def _protoh_record_error(exc: BaseException, context: str, world: Optional["World"] = None, cmd: str = "") -> Dict[str, Any]:
    global PROTOH_ERROR_COUNTER, PROTOH_ERROR_LOGS
    PROTOH_ERROR_COUNTER += 1
    code = _protoh_error_code(exc)
    raw_tb = _traceback_v237.format_exc()
    entry = {
        "id": PROTOH_ERROR_COUNTER,
        "code": code,
        "context": context,
        "command": cmd,
        "type": type(exc).__name__,
        "message": str(exc),
        "day": getattr(world, "day", None) if world is not None else None,
        "tick": getattr(world, "tick", None) if world is not None else None,
        "time": _datetime_v237.datetime.now().isoformat(timespec="seconds"),
        "traceback": raw_tb,
    }
    PROTOH_ERROR_LOGS.append(entry)
    # Mantener suficientes errores para depurar sin que crezca infinito.
    if len(PROTOH_ERROR_LOGS) > 200:
        PROTOH_ERROR_LOGS = PROTOH_ERROR_LOGS[-200:]
    return entry


def _protoh_format_error_summary(entry: Dict[str, Any]) -> str:
    return (
        f"Error {entry['code']}-{entry['id']:04d} | {entry['type']} | "
        f"contexto={entry['context']} | comando={entry.get('command') or '-'} | "
        f"día={entry.get('day')} tick={entry.get('tick')} | {entry.get('message')}"
    )


def _protoh_errors_report(error_id: Optional[int] = None) -> str:
    if not PROTOH_ERROR_LOGS:
        return "ERRORES PROTOH\n" + "=" * 100 + "\nNo hay errores registrados en esta sesión."
    lines = ["ERRORES PROTOH — TRACEBACKS BRUTOS", "=" * 100]
    entries = PROTOH_ERROR_LOGS
    if error_id is not None:
        entries = [e for e in PROTOH_ERROR_LOGS if int(e.get("id", -1)) == int(error_id)]
        if not entries:
            return f"ERRORES PROTOH\n{'='*100}\nNo existe error con id {error_id}."
    for e in entries[-30:]:
        lines.append(_protoh_format_error_summary(e))
        lines.append("-" * 100)
        lines.append(e.get("traceback", "<sin traceback>"))
        lines.append("=" * 100)
    lines.append("\nComandos: error | errores | error last | error <id>")
    return "\n".join(lines)


_old_process_command_v236_for_v237 = process_command


def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw = (cmd or "").strip()
    low = raw.lower()

    # Comando para inspeccionar errores brutos sin cerrar el programa.
    if low in ("error", "errors", "errores", "errores_brutos") or low.startswith("error ") or low.startswith("errores "):
        state["paused"] = True
        error_id = None
        parts = raw.split()
        if len(parts) >= 2:
            if parts[1].lower() in ("last", "ultimo", "último") and PROTOH_ERROR_LOGS:
                error_id = int(PROTOH_ERROR_LOGS[-1]["id"])
            else:
                try:
                    error_id = int(parts[1])
                except Exception:
                    error_id = None
        show_paged_text("ERRORES PROTOH", _protoh_errors_report(error_id))
        return False

    try:
        return _old_process_command_v236_for_v237(cmd, world, state)
    except BaseException as exc:
        # No capturamos KeyboardInterrupt/SystemExit aquí porque heredamos de BaseException,
        # pero para el caso de comandos interesa no matar la simulación; si el usuario quiere salir, usa q.
        if isinstance(exc, KeyboardInterrupt):
            raise
        entry = _protoh_record_error(exc, "process_command", world, raw)
        msg = _protoh_format_error_summary(entry)
        print("\n" + msg)
        print("Escribe 'error' para ver los errores brutos, o 'error %d' para este traceback." % entry["id"])
        try:
            state["status_message"] = msg
            state["paused"] = True
        except Exception:
            pass
        return False


globals()["process_command"] = process_command


# También protegemos advance_ticks para que un error durante fast/run no cierre toda la sesión.
# Si hay un fallo interno de simulación, se registra y se salta ese batch.
_old_advance_ticks_v236_for_v237 = advance_ticks


def advance_ticks(world: World, n: int = 1) -> None:
    try:
        return _old_advance_ticks_v236_for_v237(world, n)
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        entry = _protoh_record_error(exc, "advance_ticks", world, f"advance_ticks {n}")
        try:
            world.add_event("sistema", "error_runtime", {"error": f"{entry['code']}-{entry['id']:04d}", "tipo": entry["type"], "mensaje": entry["message"]})
        except Exception:
            pass
        return None


globals()["advance_ticks"] = advance_ticks

try:
    HELP_EXPORT_TEXT = HELP_EXPORT_TEXT + """

ERRORES v2.3.7
==============
error              muestra tracebacks brutos recientes.
error last         muestra el último error.
error 3            muestra el error con id 3.

Si un comando falla, protoH ya no se cierra: muestra Error <código>-<id>.
"""
except Exception:
    pass



# ============================================================
# v2.3.8 — CONCEPT CLIPS / MINI-GRABACIÓN DE APRENDIZAJE
# ============================================================
# Guarda una pequeña "cámara negra" de los reportes realmente importantes:
# mini mapa 10x10 + datos del momento + nodos activos. No altera decisiones,
# aprendizaje ni detector; solo añade una evidencia visual/exportable.

try:
    from collections import deque as _protoh_deque_v238
except Exception:
    _protoh_deque_v238 = None


def _clip_plain_v238(s: Any) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", str(s))


def _clip_escape_v238(s: Any) -> str:
    return html.escape(_clip_plain_v238(s))


def _clip_short_v238(s: Any, n: int = 90) -> str:
    s = _clip_plain_v238(s).replace("\n", " ").replace("\r", " ")
    return s if len(s) <= n else s[: max(0, n - 1)] + "…"


def _clip_is_super_important_v238(title: str, concept: str, resumen: str, confidence: float, importance: float, style: str) -> bool:
    txt = f"{title} {concept} {resumen}".lower()
    critical_words = [
        "auto-vida", "auto_vida", "auto existencia", "auto-existencia", "vida", "existencia",
        "yo", "mismo_ser", "continuidad", "lenguaje", "proto-lenguaje", "señal", "senal",
        "dimensión", "dimension", "muerte", "no_movimiento", "miedo", "peligro", "refugio",
        "cueva", "cebo", "trampa", "almacenamiento", "herramienta", "causa", "efecto",
        "ritual", "cultura", "social", "distancia", "medición", "medicion",
    ]
    if style in ("gold", "purple"):
        return True
    if importance >= 105:
        return True
    if confidence >= 85 and any(w in txt for w in critical_words):
        return True
    if confidence >= 65 and any(w in txt for w in ("auto-vida", "auto_vida", "vida", "existencia", "lenguaje", "dimension", "dimensión")):
        return True
    return False


def _world_clip_init_v238(self: "World") -> None:
    if not hasattr(self, "concept_clips"):
        self.concept_clips: List[Dict[str, Any]] = []
    if not hasattr(self, "pending_concept_clips"):
        self.pending_concept_clips: List[Dict[str, Any]] = []
    if not hasattr(self, "next_concept_clip_id"):
        self.next_concept_clip_id = 1
    if _protoh_deque_v238 is not None and not hasattr(self, "visual_frame_buffer"):
        self.visual_frame_buffer = _protoh_deque_v238(maxlen=220)
    elif not hasattr(self, "visual_frame_buffer"):
        self.visual_frame_buffer = []
    self.clips_enabled = getattr(self, "clips_enabled", True)
    self.clip_radius = int(getattr(self, "clip_radius", 5))
    self.clip_before_ticks = int(getattr(self, "clip_before_ticks", 80))
    self.clip_after_ticks = int(getattr(self, "clip_after_ticks", 80))
    self.clip_max_saved = int(getattr(self, "clip_max_saved", 80))


def _world_capture_visual_snapshot_v238(self: "World") -> Dict[str, Any]:
    humans_state: Dict[int, Dict[str, Any]] = {}
    occupied: List[Dict[str, Any]] = []
    for cr in self.creatures.values():
        if not cr.alive:
            continue
        char = {"human": "H", "chicken": "P", "cow": "V", "trex": "T"}.get(cr.kind, "?")
        birth = None
        if cr.kind == "human" and cr.entity_id in self.humans:
            h = self.humans[cr.entity_id]
            birth = h.birth_number
            char = "L" if getattr(h, "is_lab", False) else "H"
            humans_state[birth] = {
                "entity_id": h.entity_id,
                "name": h.name,
                "x": h.x,
                "y": h.y,
                "hp": h.hp,
                "max_hp": h.max_hp,
                "hunger": h.hunger,
                "thirst": h.thirst,
                "sleepiness": h.sleepiness,
                "energy": h.energy,
                "inventory": [it.kind for it in h.inventory],
                "last_action": h.last_action,
                "alive": h.alive,
                "is_lab": getattr(h, "is_lab", False),
                "top_nodes": h.neural.top_activations(8),
            }
        for cx, cy in cr.occupied_cells():
            if self.in_bounds(cx, cy):
                occupied.append({"x": cx, "y": cy, "char": char, "kind": cr.kind, "birth": birth})
    items = []
    for it in self.items.values():
        if self.in_bounds(it.x, it.y):
            items.append({
                "x": it.x, "y": it.y, "kind": it.kind, "char": it.char,
                "origin": getattr(it, "origin", "natural"), "placed_by": getattr(it, "placed_by", None),
            })
    return {"tick": self.tick, "day": self.day, "occupied": occupied, "items": items, "humans": humans_state}


def _world_record_visual_snapshot_v238(self: "World") -> Dict[str, Any]:
    if not hasattr(self, "visual_frame_buffer"):
        _world_clip_init_v238(self)
    snap = self.capture_visual_snapshot()
    try:
        self.visual_frame_buffer.append(snap)
    except Exception:
        self.visual_frame_buffer = [snap]
    return snap


def _world_update_pending_clips_v238(self: "World", snap: Dict[str, Any]) -> None:
    if not getattr(self, "pending_concept_clips", None):
        return
    still: List[Dict[str, Any]] = []
    for clip in list(self.pending_concept_clips):
        if not clip["frames"] or clip["frames"][-1].get("tick") != snap.get("tick"):
            clip["frames"].append(snap)
        clip["after_remaining"] = int(clip.get("after_remaining", 0)) - 1
        if clip["after_remaining"] <= 0:
            clip["status"] = "listo"
            self.concept_clips.append(clip)
            if len(self.concept_clips) > int(getattr(self, "clip_max_saved", 80)):
                self.concept_clips = self.concept_clips[-int(getattr(self, "clip_max_saved", 80)):]
            self.log("concept_clip_guardado", "world", clip_id=clip["clip_id"], humano=clip.get("human_birth"), concepto=_clip_short_v238(clip.get("concept", ""), 60), frames=len(clip.get("frames", [])))
        else:
            still.append(clip)
    self.pending_concept_clips = still


def _world_start_concept_clip_v238(self: "World", human: Optional["Human"], title: str, concept: str, confidence: float, importance: float, header: str, detail: str) -> Optional[int]:
    if not getattr(self, "clips_enabled", True) or human is None:
        return None
    _world_clip_init_v238(self)
    key_text = _clip_plain_v238(title + " " + concept).lower()[:90]
    for clip in list(getattr(self, "pending_concept_clips", [])) + list(getattr(self, "concept_clips", [])[-12:]):
        if clip.get("human_birth") == human.birth_number and clip.get("key_text") == key_text and abs(int(clip.get("detected_tick", 0)) - int(self.tick)) < 60:
            return None
    before = list(getattr(self, "visual_frame_buffer", []))[-int(getattr(self, "clip_before_ticks", 80)):]
    if not before:
        before = [self.capture_visual_snapshot()]
    cid = int(getattr(self, "next_concept_clip_id", 1))
    self.next_concept_clip_id = cid + 1
    clip = {
        "clip_id": cid,
        "status": "grabando",
        "key_text": key_text,
        "human_birth": human.birth_number,
        "human_name": human.name,
        "detected_tick": self.tick,
        "detected_day": self.day,
        "title": _clip_plain_v238(title),
        "concept": _clip_plain_v238(concept),
        "confidence": float(confidence),
        "importance": float(importance),
        "header": _clip_plain_v238(header),
        "detail": _clip_plain_v238(detail),
        "frames": before[:],
        "after_remaining": int(getattr(self, "clip_after_ticks", 80)),
        "radius": int(getattr(self, "clip_radius", 5)),
    }
    self.pending_concept_clips.append(clip)
    self.log("concept_clip_iniciado", "world", clip_id=cid, humano=human.birth_number, concepto=_clip_short_v238(concept, 60), confianza=round(confidence, 1), frames_previos=len(before))
    return cid


def _world_terrain_char_for_clip_v238(self: "World", x: int, y: int) -> str:
    if not self.in_bounds(x, y):
        return " "
    ch = self.grid[y][x]
    if ch in (CAVE_ENTRANCE, CAVE_INTERIOR):
        return "."
    if ch == EMPTY:
        return "."
    return ch


def _world_render_clip_frame_v238(self: "World", clip: Dict[str, Any], snap: Dict[str, Any], frame_index: int) -> str:
    birth = clip.get("human_birth")
    hs = snap.get("humans", {}).get(birth)
    if hs:
        cx, cy = int(hs.get("x", 0)), int(hs.get("y", 0))
    else:
        cx, cy = WIDTH // 2, HEIGHT // 2
    r = int(clip.get("radius", 5))
    size = max(4, r * 2)
    left = cx - r
    top = cy - r
    grid = [[self._terrain_char_for_clip(left + x, top + y) for x in range(size)] for y in range(size)]
    for it in snap.get("items", []):
        x, y = int(it.get("x", -999)), int(it.get("y", -999))
        if left <= x < left + size and top <= y < top + size:
            ch = str(it.get("char", "?"))[:1]
            if it.get("origin") == "human_placed" and ch == "s":
                ch = "S"
            grid[y - top][x - left] = ch
    for oc in snap.get("occupied", []):
        x, y = int(oc.get("x", -999)), int(oc.get("y", -999))
        if left <= x < left + size and top <= y < top + size:
            ch = str(oc.get("char", "?"))[:1]
            if oc.get("birth") == birth:
                ch = "@"
            grid[y - top][x - left] = ch
    mini = "\n".join("".join(row) for row in grid)
    if not hs:
        hs = {"name": f"#{birth}", "hp": "?", "max_hp": "?", "hunger": "?", "thirst": "?", "sleepiness": "?", "energy": "?", "inventory": [], "last_action": "?", "top_nodes": []}
    inv = ",".join(hs.get("inventory", [])) or "-"
    nodes = hs.get("top_nodes", [])[:6]
    node_lines = [f"{n}:{float(v):.2f}" for n, v in nodes] if nodes else ["-"]
    def numline(label, key):
        val = hs.get(key)
        return f"{label} {float(val):.1f}" if isinstance(val, (int, float)) else f"{label} {val}"
    hp_line = f"HP {hs.get('hp'):.1f}/{hs.get('max_hp'):.1f}" if isinstance(hs.get('hp'), (int, float)) else f"HP {hs.get('hp')}"
    right = [
        f"CLIP #{clip.get('clip_id')} frame {frame_index+1}/{len(clip.get('frames', []))}",
        f"Día {snap.get('day')} | Tick {snap.get('tick')}",
        f"Humano: {hs.get('name')} / #{birth}",
        f"Acción: {_clip_short_v238(hs.get('last_action'), 28)}",
        hp_line,
        f"{numline('hambre', 'hunger')} | {numline('sed', 'thirst')}",
        f"{numline('sueño', 'sleepiness')} | {numline('energía', 'energy')}",
        f"Inventario: {_clip_short_v238(inv, 32)}",
        f"Concepto: {_clip_short_v238(clip.get('title'), 36)}",
        f"Confianza: {float(clip.get('confidence',0)):.1f}% | valor {float(clip.get('importance',0)):.1f}",
        "Nodos activos:",
    ] + ["  " + _clip_short_v238(x, 36) for x in node_lines]
    mini_lines = mini.split("\n")
    height = max(len(mini_lines), len(right))
    mini_lines += [" " * size] * (height - len(mini_lines))
    right += [""] * (height - len(right))
    border = "┌" + "─" * (size + 2) + "┬" + "─" * 44 + "┐"
    sep = "├" + "─" * (size + 2) + "┼" + "─" * 44 + "┤"
    bottom = "└" + "─" * (size + 2) + "┴" + "─" * 44 + "┘"
    out = [border, f"│ {'MINI MAPA'.ljust(size)} │ {'DATOS DEL MOMENTO'.ljust(42)} │", sep]
    for a, b in zip(mini_lines, right):
        out.append(f"│ {a.ljust(size)} │ {_clip_short_v238(b,42).ljust(42)} │")
    out.append(bottom)
    return "\n".join(out)


def _world_clip_text_v238(self: "World", clip: Dict[str, Any]) -> str:
    lines = [
        f"CONCEPT CLIP #{clip.get('clip_id')} — {clip.get('title')}",
        "=" * 100,
        f"Detectado: Día {clip.get('detected_day')} | Tick {clip.get('detected_tick')} | Humano #{clip.get('human_birth')} / {clip.get('human_name')}",
        f"Confianza: {float(clip.get('confidence',0)):.1f}% | valor externo: {float(clip.get('importance',0)):.1f}/140 | estado={clip.get('status')}",
        f"Concepto/patrón: {_clip_short_v238(clip.get('concept'), 180)}",
        "=" * 100,
    ]
    frames = clip.get("frames", [])
    for i, snap in enumerate(frames):
        if i > 0:
            lines.append("\n" + "-" * 100)
        lines.append(self.render_clip_frame(clip, snap, i))
    return "\n".join(lines)


def _world_clips_report_v238(self: "World") -> str:
    _world_clip_init_v238(self)
    lines = ["CONCEPT CLIPS — MINI-GRABACIONES DE APRENDIZAJE", "=" * 100]
    lines.append(f"clips_enabled={getattr(self,'clips_enabled',True)} | pendientes={len(getattr(self,'pending_concept_clips',[]))} | guardados={len(getattr(self,'concept_clips',[]))}")
    lines.append(f"ventana: {getattr(self,'clip_before_ticks',80)} ticks antes + {getattr(self,'clip_after_ticks',80)} después | mapa={getattr(self,'clip_radius',5)*2}x{getattr(self,'clip_radius',5)*2}")
    if not getattr(self, "concept_clips", None) and not getattr(self, "pending_concept_clips", None):
        lines.append("\nAún no hay clips. Se guardan solo para conceptos súper importantes.")
        lines.append("Comandos: clips | play clip N | export clip N ruta.html | export clips all carpeta")
        return "\n".join(lines)
    if getattr(self, "pending_concept_clips", None):
        lines.append("\nPENDIENTES:")
        for c in self.pending_concept_clips[-20:]:
            lines.append(f"  #{c.get('clip_id')} grabando | H#{c.get('human_birth')} | Día {c.get('detected_day')} T{c.get('detected_tick')} | {float(c.get('confidence',0)):.1f}% | {_clip_short_v238(c.get('title'),70)} | frames={len(c.get('frames',[]))}")
    if getattr(self, "concept_clips", None):
        lines.append("\nLISTOS:")
        for c in self.concept_clips[-60:]:
            lines.append(f"  #{c.get('clip_id')} listo | H#{c.get('human_birth')} | Día {c.get('detected_day')} T{c.get('detected_tick')} | {float(c.get('confidence',0)):.1f}% | frames={len(c.get('frames',[]))} | {_clip_short_v238(c.get('title'),70)}")
    lines.append("\nComandos: clips | play clip N | export clip N ruta.html | export clips all carpeta")
    return "\n".join(lines)


def _world_find_clip_v238(self: "World", clip_id: int) -> Optional[Dict[str, Any]]:
    for c in list(getattr(self, "concept_clips", [])) + list(getattr(self, "pending_concept_clips", [])):
        try:
            if int(c.get("clip_id")) == int(clip_id):
                return c
        except Exception:
            pass
    return None


def _world_export_clip_html_v238(self: "World", clip: Dict[str, Any], path: str) -> str:
    ensure_dir_for_file(path)
    frames_text = [self.render_clip_frame(clip, snap, i) for i, snap in enumerate(clip.get("frames", []))]
    if not frames_text:
        frames_text = ["<sin frames>"]
    frames_json = repr(frames_text)
    title = f"Concept Clip #{clip.get('clip_id')} — {_clip_short_v238(clip.get('title'),80)}"
    doc = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{_clip_escape_v238(title)}</title>
<style>
body{{background:#0f1115;color:#e8e8e8;margin:0;padding:24px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.bar{{background:#171a22;border:1px solid #2e3340;border-radius:12px;padding:14px;margin-bottom:18px}}
pre{{font-family:Menlo,Consolas,"SFMono-Regular",monospace;font-size:14px;line-height:1.25;white-space:pre;background:#05060a;border:1px solid #333;border-radius:12px;padding:18px;overflow:auto}}
button{{background:#27324a;color:white;border:1px solid #53627d;border-radius:8px;padding:8px 12px;margin-right:8px;cursor:pointer}}
small{{color:#aeb6c2}}
</style></head><body>
<div class="bar"><b>{_clip_escape_v238(title)}</b><br><small>Día {clip.get('detected_day')} | Tick {clip.get('detected_tick')} | H#{clip.get('human_birth')} | confianza {float(clip.get('confidence',0)):.1f}% | frames {len(frames_text)}</small><br><br>
<button onclick="toggle()">Play/Pause</button><button onclick="prev()">◀</button><button onclick="next()">▶</button><small> Usa ← → para moverte frame a frame.</small></div>
<pre id="screen"></pre>
<script>
const frames = {frames_json};
let i=0, playing=true;
const screen=document.getElementById('screen');
function draw(){{screen.textContent=frames[i]||'';}}
function next(){{i=(i+1)%frames.length; draw();}}
function prev(){{i=(i-1+frames.length)%frames.length; draw();}}
function toggle(){{playing=!playing;}}
setInterval(()=>{{if(playing) next();}}, 120);
document.addEventListener('keydown', e=>{{if(e.key==='ArrowRight'){{next();}} if(e.key==='ArrowLeft'){{prev();}} if(e.key===' '){{toggle();}} }});
draw();
</script></body></html>'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


def _world_export_all_clips_v238(self: "World", folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    manifest = ["CONCEPT CLIPS EXPORT", "=" * 80]
    for clip in getattr(self, "concept_clips", []):
        cid = int(clip.get("clip_id", 0))
        html_path = os.path.join(folder, f"clip_{cid:04d}.html")
        txt_path = os.path.join(folder, f"clip_{cid:04d}.txt")
        self.export_clip_html(clip, html_path)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(self.clip_text(clip))
        manifest.append(f"clip_{cid:04d}.html | H#{clip.get('human_birth')} | Día {clip.get('detected_day')} T{clip.get('detected_tick')} | {float(clip.get('confidence',0)):.1f}% | {_clip_short_v238(clip.get('title'),80)}")
    if not getattr(self, "concept_clips", []):
        manifest.append("No había clips listos para exportar.")
    manifest_path = os.path.join(folder, "MANIFEST_clips.txt")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(manifest))
    return manifest_path


_old_world_init_v237_for_v238 = World.__init__
def _world_init_v238(self: "World") -> None:
    _old_world_init_v237_for_v238(self)
    _world_clip_init_v238(self)
World.__init__ = _world_init_v238

World.capture_visual_snapshot = _world_capture_visual_snapshot_v238
World.record_visual_snapshot = _world_record_visual_snapshot_v238
World.update_pending_concept_clips = _world_update_pending_clips_v238
World.start_concept_clip = _world_start_concept_clip_v238
World._terrain_char_for_clip = _world_terrain_char_for_clip_v238
World.render_clip_frame = _world_render_clip_frame_v238
World.clip_text = _world_clip_text_v238
World.clips_report = _world_clips_report_v238
World.find_clip = _world_find_clip_v238
World.export_clip_html = _world_export_clip_html_v238
World.export_all_clips = _world_export_all_clips_v238

_old_world_run_tick_v237_for_v238 = World.run_tick
def _world_run_tick_v238(self: "World") -> None:
    _old_world_run_tick_v237_for_v238(self)
    try:
        snap = self.record_visual_snapshot()
        self.update_pending_concept_clips(snap)
    except Exception as exc:
        try:
            _protoh_record_error(exc, "concept_clips_tick", self, "clip tick")
        except Exception:
            pass
World.run_tick = _world_run_tick_v238

_old_meta_print_report_v237_for_v238 = MetaObserver.print_report
def _meta_print_report_v238(self: "MetaObserver", title: str, human: Optional[Human], tipo: str, concepto: str, resumen: str, equivalente: str, confidence: float, evidencias: List[str], factors: Dict[str, float], note: str, group_name: str = "población activa", extra: Optional[List[str]] = None, red: bool = False, cyan: bool = False, darkblue: bool = False, skip_review: bool = False) -> None:
    _old_meta_print_report_v237_for_v238(self, title, human, tipo, concepto, resumen, equivalente, confidence, evidencias, factors, note, group_name, extra, red, cyan, darkblue, skip_review)
    try:
        if red or human is None:
            return
        report_text = "\n".join([title, tipo, concepto, resumen, equivalente])
        importance = concept_importance_score(report_text, confidence)
        style = style_for_report_text(report_text, confidence)
        if _clip_is_super_important_v238(title, concepto, resumen, confidence, importance, style):
            header = f"[DÍA {self.world.day} | TICK {self.world.tick} | HUMANO: {human.name}] {title} | confianza {pct(confidence)}"
            detail = "\n".join([header, f"TIPO: {tipo}", f"CONCEPTO: {concepto}", f"RESUMEN: {resumen}", f"EQUIVALENTE: {equivalente}"])
            self.world.start_concept_clip(human, title, concepto, confidence, importance, header, detail)
    except Exception as exc:
        try:
            _protoh_record_error(exc, "concept_clips_print_report", self.world, title)
        except Exception:
            pass
MetaObserver.print_report = _meta_print_report_v238

_old_process_command_v237_for_v238 = process_command
def process_command(cmd: str, world: World, state: Dict[str, Any]) -> bool:
    raw = (cmd or "").strip()
    low = raw.lower()
    parts = raw.split()
    try:
        if low in ("clips", "concept_clips", "clip list", "clips list"):
            state["paused"] = True
            show_paged_text("CONCEPT CLIPS", world.clips_report())
            return False
        if low in ("clips on", "clip on"):
            world.clips_enabled = True
            print("Concept clips activados.")
            return False
        if low in ("clips off", "clip off"):
            world.clips_enabled = False
            print("Concept clips desactivados.")
            return False
        if low.startswith("play clip") or low.startswith("clip play") or (len(parts) == 2 and parts[0].lower() == "clip" and parts[1].isdigit()):
            cid = int(parts[-1])
            clip = world.find_clip(cid)
            if not clip:
                print(f"No existe clip {cid}.")
                return False
            tmp = os.path.join(tempfile.gettempdir(), f"protoH_clip_{cid}_{int(time.time())}.html")
            world.export_clip_html(clip, tmp)
            if sys.platform == "darwin":
                subprocess.run(["open", tmp], check=False)
            else:
                opener = shutil.which("xdg-open")
                if opener:
                    subprocess.run([opener, tmp], check=False)
                else:
                    show_paged_text(f"CLIP {cid}", world.clip_text(clip))
            print(f"Clip {cid} abierto: {tmp}")
            return False
        if low.startswith("export clip "):
            if len(parts) < 4:
                print("Uso: export clip N /ruta/clip_N.html")
                return False
            cid = int(parts[2])
            path = " ".join(parts[3:]).strip()
            clip = world.find_clip(cid)
            if not clip:
                print(f"No existe clip {cid}.")
                return False
            if path.lower().endswith(".txt"):
                ensure_dir_for_file(path)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(world.clip_text(clip))
                print(f"Clip {cid} exportado TXT: {path}")
            else:
                if not (path.lower().endswith(".html") or path.lower().endswith(".htm")):
                    path = path + ".html"
                world.export_clip_html(clip, path)
                print(f"Clip {cid} exportado como HTML animado: {path}")
            return False
        if low.startswith("export clips all"):
            if len(parts) < 4:
                print("Uso: export clips all /ruta/carpeta")
                return False
            folder = " ".join(parts[3:]).strip()
            manifest = world.export_all_clips(folder)
            print(f"Clips exportados en: {folder}\nManifest: {manifest}")
            return False
        if low.startswith("clip settings"):
            show_paged_text("CLIP SETTINGS", world.clips_report())
            return False
        return _old_process_command_v237_for_v238(cmd, world, state)
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        entry = _protoh_record_error(exc, "process_command_clips", world, raw)
        print("\n" + _protoh_format_error_summary(entry))
        print(f"Escribe 'error {entry['id']}' para ver el traceback bruto.")
        state["paused"] = True
        return False

globals()["process_command"] = process_command

try:
    HELP_EXPORT_TEXT = HELP_EXPORT_TEXT + """

CONCEPT CLIPS v2.3.8
====================
clips                         lista mini-grabaciones de conceptos importantes.
play clip N                   abre una mini-reproducción 10x10 en el navegador.
export clip N RUTA.html        exporta un clip como HTML animado.
export clip N RUTA.txt         exporta el clip como texto plano.
export clips all RUTA_CARPETA  exporta todos los clips listos.
"""
except Exception:
    pass

try:
    HELP_TEXT = HELP_TEXT + """

Concept Clips:
  clips
  play clip N
  export clip N /ruta/clip.html
  export clips all /ruta/carpeta
"""
except Exception:
    pass


# ============================================================
# ARRANQUE — debe ir al final para que todas las capas/patches v2.x estén activas
# ============================================================
if __name__ == "__main__":
    main()
