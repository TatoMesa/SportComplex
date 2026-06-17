from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.complexes.models import Complex
from .forms import MatchResultForm, TeamForm, TournamentCategoryForm, TournamentForm
from .models import Match, Team, Tournament, TournamentCategory


class TournamentSelectComplexView(LoginRequiredMixin, ListView):
    template_name = "tournaments/select_complex.html"
    context_object_name = "complexes"

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Complex.objects.all()
        return Complex.objects.filter(owner=user)

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if qs.count() == 1:
            return redirect("tournaments:list", slug=qs.first().slug)
        return super().get(request, *args, **kwargs)


class TournamentListView(LoginRequiredMixin, ListView):
    model = Tournament
    template_name = "tournaments/list.html"
    context_object_name = "tournaments"

    def dispatch(self, request, *args, **kwargs):
        self.complex = get_object_or_404(Complex, slug=kwargs["slug"])
        if not request.user.is_super_admin and self.complex.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Tournament.objects.filter(
            complex=self.complex
        ).select_related("sport").order_by("-start_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["complex"] = self.complex
        return ctx


class TournamentCreateView(LoginRequiredMixin, CreateView):
    model = Tournament
    form_class = TournamentForm
    template_name = "tournaments/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.complex = get_object_or_404(Complex, slug=kwargs["slug"])
        if not request.user.is_super_admin and self.complex.owner != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.complex = self.complex
        messages.success(self.request, "Torneo creado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("tournaments:detail", kwargs={
            "slug": self.complex.slug, "pk": self.object.pk
        })

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["complex"] = self.complex
        ctx["page_title"] = "Nuevo torneo"
        ctx["submit_label"] = "Crear torneo"
        return ctx


class TournamentDetailView(LoginRequiredMixin, DetailView):
    model = Tournament
    template_name = "tournaments/detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.complex = get_object_or_404(Complex, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["complex"] = self.complex
        ctx["categories"] = self.object.categories.prefetch_related(
            "teams", "matches__team_a", "matches__team_b", "matches__winner"
        )
        ctx["category_form"] = TournamentCategoryForm()
        return ctx


class AddCategoryView(LoginRequiredMixin, View):
    def post(self, request, slug, pk):
        complex = get_object_or_404(Complex, slug=slug)
        tournament = get_object_or_404(Tournament, pk=pk, complex=complex)
        if not request.user.is_super_admin and complex.owner != request.user:
            raise PermissionDenied

        form = TournamentCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.tournament = tournament
            cat.save()
            messages.success(request, f"Categoría '{cat.name}' creada.")
        return redirect("tournaments:detail", slug=slug, pk=pk)


class AddTeamView(LoginRequiredMixin, View):
    def post(self, request, slug, pk, cat_pk):
        complex = get_object_or_404(Complex, slug=slug)
        category = get_object_or_404(TournamentCategory, pk=cat_pk)
        if not request.user.is_super_admin and complex.owner != request.user:
            raise PermissionDenied

        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.category = category
            team.save()
            messages.success(request, f"Equipo '{team.name}' inscripto.")
        return redirect("tournaments:detail", slug=slug, pk=pk)


class GenerateFixtureView(LoginRequiredMixin, View):
    def post(self, request, slug, pk, cat_pk):
        complex = get_object_or_404(Complex, slug=slug)
        category = get_object_or_404(TournamentCategory, pk=cat_pk)
        if not request.user.is_super_admin and complex.owner != request.user:
            raise PermissionDenied

        from services.fixture_generator import generate_fixture
        matches = generate_fixture(category)
        messages.success(request, f"Fixture generado con {len(matches)} partidos.")
        return redirect("tournaments:detail", slug=slug, pk=pk)


class UpdateMatchResultView(LoginRequiredMixin, View):
    def post(self, request, slug, pk, match_pk):
        complex = get_object_or_404(Complex, slug=slug)
        match = get_object_or_404(Match, pk=match_pk)
        if not request.user.is_super_admin and complex.owner != request.user:
            raise PermissionDenied

        try:
            score_a = int(request.POST.get("score_a", 0))
            score_b = int(request.POST.get("score_b", 0))
        except (ValueError, TypeError):
            messages.error(request, "Resultado inválido.")
            return redirect("tournaments:detail", slug=slug, pk=pk)

        match.score_a = score_a
        match.score_b = score_b
        match.status = "FINISHED"

        # Ganador automático por score
        if score_a > score_b:
            match.winner = match.team_a
        elif score_b > score_a:
            match.winner = match.team_b
        else:
            match.winner = None  # empate

        match.save()
        messages.success(request, "Resultado guardado.")
        return redirect("tournaments:detail", slug=slug, pk=pk)