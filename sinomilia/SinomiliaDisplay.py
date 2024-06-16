import numpy as np
from colorama import Style, Fore, Back, init
import random
import itertools

# def move_to_str(move):
# 	if   move < 15:
# 		return f'buy {cards_description[move][-1]}'
# 	elif move < 15+4:
# 		i = move-15
# 		return f'enable {monuments_description[i][-1]}'
# 	elif move == 15+4:
# 		return f'roll dice(s) again'
# 	else:
# 		return f'do nothing'

############################# NAMES ######################################

cards_description = [
	(Back.BLUE   , Fore.WHITE, '  1  ', 1, 'banque → 1 → tous'     , 'champs de blé'             ), # 0
	(Back.BLUE   , Fore.WHITE, '  2  ', 1, 'banque → 1 → tous'     , 'ferme'                     ), # 1
	(Back.GREEN  , Fore.WHITE, ' 2-3 ', 1, 'banque → 1 → moi '     , 'boulangerie'               ), # 2
	(Back.RED    , Fore.WHITE, '  3  ', 2, 'lanceur → 1 → moi'     , 'café'                      ), # 3
	(Back.GREEN  , Fore.WHITE, '  4  ', 2, 'banque → 3 → moi'      , 'supérette'                 ), # 4
	(Back.BLUE   , Fore.WHITE, '  5  ', 3, 'banque → 1 → tous'     , 'forêt'                     ), # 5
	(Back.MAGENTA, Fore.WHITE, '  6  ', 6, 'tous → 2 → moi'        , 'stade'                     ), # 6
	(Back.MAGENTA, Fore.WHITE, '  6  ', 8, 'qqun ⇆ 1 carte ⇆ moi'  , 'centre d\'affaires'        ), # 7
	(Back.MAGENTA, Fore.WHITE, '  6  ', 7, 'qqun → 5 → moi'        , 'chaîne de télévision'      ), # 8
	(Back.GREEN  , Fore.WHITE, '  7  ', 5, 'banque → 3*c2 → moi'   , 'fromagerie'                ), # 9
	(Back.GREEN  , Fore.WHITE, '  8  ', 3, 'banque → 3*c5&9 → moi' , 'fabrique de meubles'       ), # 10
	(Back.BLUE   , Fore.WHITE, '  9  ', 6, 'banque → 5 → tous '    , 'mine'                      ), # 11
	(Back.RED    , Fore.WHITE, ' 9-10', 3, 'lanceur → 2 → moi '    , 'restaurant'                ), # 12
	(Back.BLUE   , Fore.WHITE, '  10 ', 3, 'banque → 3 → tous '    , 'verger'                    ), # 13
	(Back.GREEN  , Fore.WHITE, '11-12', 2, 'banque → 2*c1&10 → moi', 'marché de fruits & légumes'), # 14
]

monuments_description = [
	(Back.YELLOW, Fore.BLACK, 4,  '2 dés'                      , 'gare'               ), # 0
	(Back.YELLOW, Fore.BLACK, 10, 'bonus c2-3 & 3 & 4 & 9-10'  , 'centre commercial'  ), # 1
	(Back.YELLOW, Fore.BLACK, 16, 'tour bonus si double'       , 'tour radio'         ), # 2
	(Back.YELLOW, Fore.BLACK, 22, 'peut relancer dés'          , 'parc d\'attractions'), # 3
]

############################# PRINT GAME ######################################

# def _print_round_and_scores(board):
# 	n = board.num_players
# 	print('='*10, f' round {board.get_round()}    ', end='')
# 	for p in range(n):
# 		print(f'{Style.BRIGHT}P{p}{Style.RESET_ALL}: {board.get_score(p)} points  ', end='')
# 	print('='*10, Style.RESET_ALL)

# def _print_values(array_with_two_values):
# 	current_value, past_value = array_with_two_values[0], array_with_two_values[1]
# 	if current_value > 0 or current_value != past_value:
# 		print(f'{Style.BRIGHT}{current_value}', end='')
# 		if current_value != past_value:
# 			print(f'{Style.DIM}({past_value}){Style.RESET_ALL}  ', end='')
# 		else:
# 			print(f'{Style.RESET_ALL}     ', end='')
# 	else:
# 		print(f'      ', end='')

# def _print_card(board, i):
# 	color_back, color_front, dice_value, cost, descr, full_name = cards_description[i]
# 	print(f'{Style.DIM}{full_name[:25]:25}{Style.NORMAL} {descr:25} {cost}$  {color_back}{color_front}{dice_value}{Style.RESET_ALL} : ', end='')
# 	for p in range(board.num_players):
# 		_print_values(board.players_cards[15*p+i])
# 	_print_values(board.market[i])
# 	print()

# def _print_monument(board, i):
# 	color_back, color_front, cost, descr, full_name = monuments_description[i]
# 	print(f'{Style.DIM}{full_name[:25]:25}{Style.NORMAL} {descr:25} {cost:2}$ {color_back}{color_front}  M{i} {Style.RESET_ALL} : ', end='')
# 	for p in range(board.num_players):
# 		_print_values(board.players_monuments[4*p+i])
# 	print()

# def _print_money_and_misc(board):
# 	print(f'{" "*56}Money : ', end='')
# 	for p in range(board.num_players):
# 		print(f'{Style.BRIGHT}{board.players_money[p,0]:2}$   ', end='')
# 	print(f'       ', end='')
# 	print(f'{Style.DIM}dice {Style.RESET_ALL}{board.last_dice[0]}  ', end='')
# 	print(f'{Style.DIM}state {Style.RESET_ALL}{board.player_state[0]}', end='')
# 	print()

# def _print_main(board):
# 	# Print titles
# 	print(" "*26 + "Effet                    Cost  🎲 ", end='')
# 	for p in range(board.num_players):
# 		print(f'    P{p}', end='')
# 	print(f'  Market', end='')
# 	print()

# 	# Print values for each card
# 	for i in range(len(cards_description)):
# 		_print_card(board, i)

# 	# Print values for each monument
# 	for i in range(len(monuments_description)):
# 		_print_monument(board, i)

# 	# Print money and misc
# 	_print_money_and_misc(board)

init(autoreset=True)

def print_board(board):
	print()
	_print_round_and_scores(board)
	_print_main(board)

def _print_round_and_scores(board):
	round_number = board.round
	p1_score = board.p1_chips
	p2_score = board.p2_chips
	print(f"{Style.BRIGHT}Round: {Fore.YELLOW}{round_number}")
	print(f"{Style.BRIGHT}Player 1 Chips: {Fore.GREEN}{p1_score}")
	print(f"{Style.BRIGHT}Player 2 Chips: {Fore.GREEN}{p2_score}")
	print()

def _print_main(board):
	p1_hand = _get_hand_representation(board.p1_cards)
	p2_hand = _get_hand_representation(board.p2_cards)
	chips_bet_total = board.chips_bet_total
	moon_chips_bet_total = board.moon_chips_bet_total
	start_player = f"{Fore.CYAN}Player 1" if board.start_player == 0 else f"{Fore.CYAN}Player 2"
	pass_active = f"{Fore.RED}Yes" if board.pass_active else "No"
	moon_chip_active = f"{Fore.RED}Yes" if board.moon_chip_active else "No"
	played_card_number = board.played_card_number

	print(f"{Style.BRIGHT}Player 1 Hand: {Fore.MAGENTA}{p1_hand}")
	print(f"{Style.BRIGHT}Player 2 Hand: {Fore.MAGENTA}{p2_hand}")
	print(f"{Style.BRIGHT}Total Chips Bet: {Fore.BLUE}{chips_bet_total}")
	print(f"{Style.BRIGHT}Total Moon Chips Bet: {Fore.BLUE}{moon_chips_bet_total}")
	print(f"{Style.BRIGHT}Start Player: {start_player}")
	print(f"{Style.BRIGHT}Pass Active: {pass_active}")
	print(f"{Style.BRIGHT}Moon Chip Active: {moon_chip_active}")
	print(f"{Style.BRIGHT}Played Card Number: {Fore.YELLOW}{played_card_number}")
	print()

def _get_hand_representation(cards):
	return " ".join(str(card) for card in cards)

# # Example usage
# class MockBoard:
# 	def __init__(self):
# 		self.round = 1
# 		self.p1_chips = 5
# 		self.p2_chips = 3
# 		self.p1_cards = [0, 0, 1, 0, 1, 0, 1, 0, 0, 0]
# 		self.p2_cards = [1, 1, 0, 0, 0, 1, 0, 0, 1, 1]
# 		self.chips_bet_total = 4
# 		self.moon_chips_bet_total = 2
# 		self.start_player = 0
# 		self.pass_active = 0
# 		self.moon_chip_active = 1
# 		self.played_card_number = 5

# board = MockBoard()
# print_board(board)

def print_board(board):
	print()
	_print_round_and_scores(board)
	_print_main(board)
