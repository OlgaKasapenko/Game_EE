from otree.api import *

class C(BaseConstants):
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 30
    NAME_IN_URL = 'game_risks_2'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    current_guess = models.BooleanField()

class Player(BasePlayer):
    guess = models.BooleanField(
        choices=[[True, 'Рискнуть'], [False, 'Забрать деньги']],
        doc="""This player's decision""",
        widget=widgets.RadioSelect,
    )
    money = models.CurrencyField(initial=100)
    last_step_was_last = models.BooleanField(initial=False)
    prob = models.CurrencyField(initial=1)

# FUNCTIONS

def set_payoffs(group: Group):
    import random
    players = group.get_players()
    p = players[0]
    current_guess = p.field_maybe_none('guess')

    if p.round_number > 1:
        previous_player = p.in_all_rounds()[-2]
        if previous_player.last_step_was_last == False:
            p.money = previous_player.money
        else:
            p.money = 100

    if current_guess == True:
        p.prob = (6 - p.round_number) % 5
        p.payoff = random.choices([2 * p.money, 0], weights=[(5 - p.round_number) % 5, 1])[0]
        if p.payoff == 0:
            p.last_step_was_last = True
        else:
            p.last_step_was_last = False
    else:
        p.payoff = p.money
        p.last_step_was_last = True
    group.current_guess = current_guess
    p.money = p.payoff



def action_history(player: Player):
    return [p.field_maybe_none('guess') for p in player.in_all_rounds()]


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Guess(Page):
    form_model = 'player'
    form_fields = ['guess']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(action_history=action_history(player))

    @staticmethod
    def is_displayed(player: Player):
        return True


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

    @staticmethod
    def before_next_page(group: Group, player: Player):
        players = group.get_players()

class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        group = player.group

        # Получаем монеты из всех предыдущих раундов
        previous_rounds_money = [p.money for p in player.in_all_rounds()[:-1]]  # все раунды, кроме последнего

page_sequence = [Introduction, Guess, ResultsWaitPage, Results]

