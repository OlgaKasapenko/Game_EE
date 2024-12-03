from otree.api import *

doc = """
Игра с рисками: игроки в каждом раунде решают рискнуть или забрать текущие деньги.
При риске с вероятностью 3/4 сумма удваивается, с вероятностью 1/4 обнуляется.
"""

class C(BaseConstants):
    NAME_IN_URL = 'game_risks'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 30
    INITIAL_AMOUNT = cu(100)
    SUCCESS_RATE = 0.75

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    current_amount = models.CurrencyField(
        initial=C.INITIAL_AMOUNT,
        doc="Текущая сумма денег"
    )
    
    total_payoff = models.CurrencyField(
        initial=cu(0),
        doc="Общий выигрыш за игру"
    )
    
    choice = models.BooleanField(
        choices=[
            [True, 'Рискнуть'],
            [False, 'Забрать деньги']
        ],
        doc="Решение игрока в текущем раунде",
        widget=widgets.RadioSelect
    )
    
    round_result = models.StringField(
        doc="Описание результата раунда"
    )
    
    success = models.BooleanField(
        doc="Успех при риске (если был риск)"
    )

    def play_round(self):
        import random
        
        round_index = (self.round_number - 1) % 5
        success_rates = [0.8, 0.6, 0.4, 0.2, 0.0]
        current_success_rate = success_rates[round_index]
        
        initial_amount = self.current_amount
        
        if self.choice:  # Игрок рискнул
            self.success = random.random() < current_success_rate
            if self.success:  # Успех
                self.current_amount *= 2
                self.round_result = f"Рискнул с {initial_amount}. Успех! Получил {self.current_amount}"
                if self.round_number < C.NUM_ROUNDS:
                    self.in_round(self.round_number + 1).current_amount = self.current_amount
                    self.in_round(self.round_number + 1).total_payoff = self.total_payoff
            else:  # Неудача
                self.current_amount = C.INITIAL_AMOUNT
                self.round_result = f"Рискнул с {initial_amount}. Неудача. Следующий раунд начнет с {C.INITIAL_AMOUNT}"
                if self.round_number < C.NUM_ROUNDS:
                    self.in_round(self.round_number + 1).current_amount = C.INITIAL_AMOUNT
                    self.in_round(self.round_number + 1).total_payoff = self.total_payoff
        else:  # Игрок забрал деньги
            self.total_payoff += self.current_amount
            self.round_result = f"Забрал {self.current_amount}. Общий выигрыш: {self.total_payoff}"
            self.current_amount = C.INITIAL_AMOUNT
            if self.round_number < C.NUM_ROUNDS:
                self.in_round(self.round_number + 1).current_amount = C.INITIAL_AMOUNT
                self.in_round(self.round_number + 1).total_payoff = self.total_payoff
            self.payoff = self.total_payoff

# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class GamePage(Page):
    form_model = 'player'
    form_fields = ['choice']

    @staticmethod
    def vars_for_template(player: Player):
        previous_result = ''
        if player.round_number > 1:
            prev_player = player.in_round(player.round_number - 1)
            previous_result = prev_player.round_result
            player.total_payoff = prev_player.total_payoff

        round_index = (player.round_number - 1) % 5
        success_rates = [0.8, 0.6, 0.4, 0.2, 0.0]
        current_success_rate = success_rates[round_index]
        success_percentage = int(current_success_rate * 100)

        return {
            'current_amount': player.current_amount,
            'total_payoff': player.total_payoff,
            'round_number': player.round_number,
            'previous_result': previous_result,
            'success_rate': success_percentage
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.play_round()

class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        all_rounds = []
        for p in player.in_all_rounds():
            round_index = (p.round_number - 1) % 5
            success_rates = [0.8, 0.6, 0.4, 0.2, 0.0]
            success_rate = int(success_rates[round_index] * 100)
            
            all_rounds.append({
                'round_number': p.round_number,
                'initial_amount': p.current_amount,
                'choice': 'Рискнул' if p.choice else 'Забрал деньги',
                'final_amount': p.current_amount * 2 if (p.choice and p.success) else C.INITIAL_AMOUNT,
                'total_payoff': p.total_payoff,
                'result': p.round_result,
                'success_rate': success_rate
            })
        
        return {
            'all_rounds': all_rounds,
            'final_payoff': player.total_payoff
        }

class FinalResults(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        all_players_results = []
        for p in player.subsession.get_players():
            player_rounds = []
            for round_p in p.in_all_rounds():
                round_index = (round_p.round_number - 1) % 5
                success_rates = [0.8, 0.6, 0.4, 0.2, 0.0]
                success_rate = int(success_rates[round_index] * 100)
                
                player_rounds.append({
                    'round_number': round_p.round_number,
                    'initial_amount': round_p.current_amount,
                    'choice': 'Рискнул' if round_p.choice else 'Забрал деньги',
                    'final_amount': round_p.current_amount * 2 if (round_p.choice and round_p.success) else C.INITIAL_AMOUNT,
                    'total_payoff': round_p.total_payoff,
                    'result': round_p.round_result,
                    'success_rate': success_rate  # Добавляем вероятность успеха
                })
            all_players_results.append({
                'player_id': p.id_in_subsession,
                'rounds': player_rounds,
                'final_payoff': p.total_payoff
            })
        
        return {
            'all_players_results': all_players_results
        }

page_sequence = [Introduction, GamePage, Results, FinalResults]

