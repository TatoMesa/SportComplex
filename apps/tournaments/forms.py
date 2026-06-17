from django import forms
from .models import Match, Team, Tournament, TournamentCategory

INPUT_CLASS = (
    "w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-primary-500 "
    "focus:border-transparent transition"
)


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ["name", "sport", "format", "status", "start_date", "end_date", "max_teams", "description", "prize_info"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "sport": forms.Select(attrs={"class": INPUT_CLASS}),
            "format": forms.Select(attrs={"class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
            "start_date": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}, format="%Y-%m-%d"),
            "max_teams": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 3}),
            "prize_info": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].input_formats = ["%Y-%m-%d"]
        self.fields["end_date"].input_formats = ["%Y-%m-%d"]


class TournamentCategoryForm(forms.ModelForm):
    class Meta:
        model = TournamentCategory
        fields = ["name", "description", "max_teams"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
            "max_teams": forms.NumberInput(attrs={"class": INPUT_CLASS}),
        }


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "seed"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Ej: Los Cracks"}),
            "seed": forms.NumberInput(attrs={"class": INPUT_CLASS}),
        }


class MatchResultForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["score_a", "score_b", "winner", "status", "notes"]
        widgets = {
            "score_a": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "score_b": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "winner": forms.Select(attrs={"class": INPUT_CLASS}),
            "status": forms.Select(attrs={"class": INPUT_CLASS}),
            "notes": forms.Textarea(attrs={"class": INPUT_CLASS, "rows": 2}),
        }

    def __init__(self, *args, match=None, **kwargs):
        super().__init__(*args, **kwargs)
        if match:
            teams = []
            if match.team_a:
                teams.append((match.team_a.pk, match.team_a.name))
            if match.team_b:
                teams.append((match.team_b.pk, match.team_b.name))
            self.fields["winner"].choices = [("", "— Sin ganador —")] + teams