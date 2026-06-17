from django.contrib import admin
from .models import Match, Team, Tournament, TournamentCategory


class TournamentCategoryInline(admin.TabularInline):
    model = TournamentCategory
    extra = 1
    fields = ("name", "max_teams")


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "complex", "sport", "format", "status", "start_date")
    list_filter = ("status", "format", "sport")
    search_fields = ("name", "complex__name")
    inlines = [TournamentCategoryInline]


class MatchInline(admin.TabularInline):
    model = Match
    extra = 0
    fields = ("round_number", "team_a", "team_b", "score_a", "score_b", "winner", "status")


@admin.register(TournamentCategory)
class TournamentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tournament", "max_teams")
    inlines = [MatchInline]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "seed")
    filter_horizontal = ("players",)