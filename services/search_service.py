"""
Servicio de búsqueda global de canchas disponibles.
Recibe filtros y devuelve canchas con su disponibilidad,
priorizando complejos favoritos del usuario.
"""

from datetime import date, time
from typing import Optional

from django.db.models import Q, QuerySet

from apps.complexes.models import Complex, Court, Sport
from apps.reservations.models import Reservation, ReservationStatus


def get_available_courts(
    search_date: date,
    start_time: time,
    end_time: time,
    sport_id: Optional[int] = None,
    city: Optional[str] = None,
    max_price: Optional[float] = None,
    complex_id: Optional[str] = None,
    user=None,
) -> list[dict]:
    """
    Retorna canchas disponibles para el horario solicitado.
    Cada ítem incluye la cancha, el complejo y si el usuario la tiene como favorita.
    """

    # Base: canchas activas en complejos activos
    courts = Court.objects.select_related(
        "complex__owner", "sport"
    ).filter(
        is_active=True,
        complex__status="ACTIVE",
    )

    # Filtros opcionales
    if sport_id:
        courts = courts.filter(sport_id=sport_id)

    if city:
        courts = courts.filter(complex__city__icontains=city)

    if max_price:
        courts = courts.filter(price_per_hour__lte=max_price)

    if complex_id:
        courts = courts.filter(complex_id=complex_id)

    # Excluir canchas con reservas activas que se solapen con el horario pedido
    busy_court_ids = Reservation.objects.filter(
        date=search_date,
        status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
        start_time__lt=end_time,
        end_time__gt=start_time,
    ).values_list("court_id", flat=True)

    courts = courts.exclude(id__in=busy_court_ids)

    # Favoritos del usuario
    favorite_complex_ids = set()
    if user and user.is_authenticated:
        from apps.accounts.models import FavoriteComplex
        favorite_complex_ids = set(
            FavoriteComplex.objects.filter(user=user).values_list("complex_id", flat=True)
        )

    # Armar resultados con metadata
    results = []
    for court in courts:
        is_favorite = court.complex_id in favorite_complex_ids
        results.append({
            "court": court,
            "complex": court.complex,
            "sport": court.sport,
            "is_favorite": is_favorite,
            "price_per_hour": court.price_per_hour,
        })

    # Ordenar: favoritos primero, luego por precio
    results.sort(key=lambda x: (not x["is_favorite"], x["price_per_hour"]))

    return results


def get_sports_with_courts() -> QuerySet:
    """Deportes que tienen al menos una cancha activa."""
    return Sport.objects.filter(
        courts__is_active=True,
        courts__complex__status="ACTIVE",
    ).distinct().order_by("name")


def get_active_cities() -> list[str]:
    """Ciudades con complejos activos."""
    return list(
        Complex.objects.filter(status="ACTIVE")
        .values_list("city", flat=True)
        .distinct()
        .order_by("city")
    )