"""
Generador de fixtures por formato de torneo.
Separado de las vistas para poder testearlo independientemente.
"""

import math
from typing import List

from apps.tournaments.models import Match, MatchStatus, Team, TournamentCategory


def generate_round_robin(category: TournamentCategory) -> List[Match]:
    """
    Genera fixture Round Robin: todos contra todos.
    Algoritmo de rotación circular.
    """
    teams = list(category.teams.all())
    n = len(teams)
    if n < 2:
        return []

    # Si número impar, agregar BYE
    if n % 2 != 0:
        teams.append(None)
        n += 1

    matches = []
    rounds = n - 1
    half = n // 2

    for round_num in range(rounds):
        for i in range(half):
            team_a = teams[i]
            team_b = teams[n - 1 - i]
            if team_a is not None and team_b is not None:
                match = Match(
                    category=category,
                    round_number=round_num + 1,
                    match_number=i + 1,
                    team_a=team_a,
                    team_b=team_b,
                    status=MatchStatus.PENDING,
                )
                matches.append(match)
        # Rotar equipos (el primero fijo)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

    Match.objects.bulk_create(matches)
    return matches


def generate_single_elimination(category: TournamentCategory) -> List[Match]:
    """
    Genera fixture de eliminación simple.
    Rellena con BYE si no es potencia de 2.
    """
    teams = list(category.teams.order_by("seed", "name"))
    n = len(teams)
    if n < 2:
        return []

    # Redondear al próximo power of 2
    bracket_size = 2 ** math.ceil(math.log2(n))
    # Rellenar con None (BYE)
    teams += [None] * (bracket_size - n)

    matches = []
    round_num = 1
    match_num = 1

    for i in range(0, bracket_size, 2):
        team_a = teams[i]
        team_b = teams[i + 1]
        # Si uno es BYE, el otro pasa automáticamente
        if team_a is None or team_b is None:
            continue
        match = Match(
            category=category,
            round_number=round_num,
            match_number=match_num,
            team_a=team_a,
            team_b=team_b,
            status=MatchStatus.PENDING,
        )
        matches.append(match)
        match_num += 1

    Match.objects.bulk_create(matches)
    return matches


def generate_fixture(category: TournamentCategory) -> List[Match]:
    """Entry point — elige el generador según el formato del torneo."""
    format_ = category.tournament.format

    # Limpiar partidos anteriores si se regenera
    category.matches.all().delete()

    from apps.tournaments.models import TournamentFormat
    generators = {
        TournamentFormat.ROUND_ROBIN: generate_round_robin,
        TournamentFormat.SINGLE_ELIMINATION: generate_single_elimination,
        TournamentFormat.DOUBLE_ELIMINATION: generate_single_elimination,  # simplificado por ahora
        TournamentFormat.AMERICANO: generate_round_robin,
        TournamentFormat.MEXICANO: generate_round_robin,
    }

    generator = generators.get(format_, generate_round_robin)
    return generator(category)