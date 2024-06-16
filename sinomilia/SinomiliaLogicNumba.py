import numpy as np
from numba import njit
import numba

############################## BOARD DESCRIPTION ##############################
# Board is described by a numba array.
# For development, players are referred to as 1 and 2, but the input values are normalized to 0 or 1 where possible.
# There are several limitations: moon chips are not used, bonuses for winning with 0 or 1 chips left are not used
# 
##### Index  Shortcut              	Meaning
#####  0-9   self.p1_cards          Cards in the hand of player 1, 0 if the card is in play or in hand, 1 if the card card has been used
##### 10-19  self.p2_cards          Cards in the hand of player 2, 0 if the card is in play or in hand, 1 if the card card has been used
#####  20    self.start_player      0 or 1, depending on who went first in the current round
#####  21    self.pass_active	      0 or 1, depending on whether the preceding player passed
#####  22    self.p1_changed        0 or 1, 1 after p1 has changed cards in the current round
#####  23    self.p2_changed        0 or 1, 1 after p2 has changed cards in the current round
#####  24    self.p1_chips          Number of chips in bank for p1
#####  25    self.p2_chips          Number of chips in bank for p2
#####  26    self.p1_chips_bet      Number of chips bet by p1 in current round
#####  27    self.p2_chips_bet      Number of chips bet by p2 in current round
#####  28    self.chips_bet_total   Number of chips bet in total in current round
#####  29    self.moon_chips_bet_total    Number of moon chips bet in total in current round
#####  30    self.moon_chip_active  0 or 1, 1 if the last play was a moon chip
#####  31    self.p1_cards_total    Number of cards in hand+play for player 1
#####  32    self.p2_cards_total    Number of cards in hand+play for player 2
#####  33    self.p1_nines_total    Number of times 9 has been played for player 1
#####  34    self.p2_nines_total    Number of times 9 has been played for player 2
#####  35    self.played_card_number    Card number chosen by the currently active player
#####  36    self.round             Current round number; used for MCTS optimization
#
# There's also hidden state:
# self.selected_cards  2 element array, -1 means the player doesn't have a card chosen yet (start of game, after round, after playing change)

############################## ACTION DESCRIPTION #############################
# There are 13 actions. Here is description of each action:
##### Index  Meaning
#####   0    Select the 0 card
#####   1    Select the 1 card
#####  ...
#####   9    Select the 9 card
#####  10    Pass
#####  11    Play chip
#####  12    Play moon chip
#####  13    Change card

@njit(cache=True, fastmath=True, nogil=True)
def observation_size(num_players):
	return (37, 2) # 2nd dimension is to keep history of previous states

@njit(cache=True, fastmath=True, nogil=True)
def action_size():
	return 13

@njit(cache=True, fastmath=True, nogil=True)
def my_random_choice_and_normalize(prob):
	normalized_prob = prob / prob.sum()
	result = np.searchsorted(np.cumsum(prob), np.random.random(), side="right")
	return result


spec = [
	('state', numba.int8[:,:]),
	('p1_cards', numba.int8[:]),
	('p2_cards', numba.int8[:]),
	('start_player', numba.int8[:]),
	('pass_active', numba.int8[:]),
	('p1_changed', numba.int8[:]),
	('p2_changed', numba.int8[:]),
	('p1_chips', numba.int8[:]),
	('p2_chips', numba.int8[:]),
	('p1_chips_bet', numba.int8[:]),
	('p2_chips_bet', numba.int8[:]),
	('chips_bet_total', numba.int8[:]),
	('moon_chips_bet_total', numba.int8[:]),
	('moon_chip_active', numba.int8[:]),
	('p1_cards_total', numba.int8[:]),
	('p2_cards_total', numba.int8[:]),
	('self.p1_nines_total', numba.int8[:]),
	('self.p2_nines_total', numba.int8[:]),
	('self.played_card_number', numba.int8[:]),
	('self.round', numba.int8[:]),
]
@numba.experimental.jitclass(spec)
class Board():
	def __init__(self, num_players):
		self.num_players = num_players
		self.current_player_index = 0
		self.selected_cards = [-1, -1]
		self.state = np.zeros(observation_size(self.num_players), dtype=np.int8)
		self.init_game()

	def init_game(self):
		self.copy_state(np.zeros(observation_size(self.num_players), dtype=np.int8), copy_or_not=False)
		self.p1_chips = 15
		self.p2_chips = 15
		self.p1_cards_total = 10
		self.p2_cards_total = 10
  
	def get_state(self):
		return self.state

	def valid_moves(self, player):
		"""
		Returns a boolean array representing the validity of each possible action for the given player.

		:param player: The current player.
		:return: A boolean array where each index represents whether the corresponding action is valid.
		"""
		result = np.zeros(14, dtype=np.bool_)
		result[0:10] = self._valid_select_card(player)
		result[10] = self._valid_pass(player)
		result[11] = self._valid_play_chip(player)
		result[12] = self._valid_play_chip(player)
		result[13] = self._valid_change_card(player)
		return result

	def _valid_select_card(self, player):
		"""
		Determine the validity of selecting each card (0-9) for the given player.
		:return: A boolean array where each index represents whether selecting the corresponding card is valid.
		"""
		if (self.selected_cards[player] != -1):
			return np.zeros(10, dtype=np.bool_)
		valid = np.zeros(10, dtype=np.bool_)
		for i in range(10):
				valid[i] = self.state[player * 10 + i] == 0
		return valid

	def _valid_pass(self, player):
		"""Determine the validity of passing for the given player."""
		return self.selected_cards[player] != -1

	def _valid_play_chip(self, player):
		"""Determine the validity of playing a chip for the given player."""
		return self._valid_pass(player) and self.chips_bet_total < 9 and (self.p1_chips > 0 if player == 0 else self.p2_chips > 0)

	def _valid_change_card(self, player):
		"""Determine the validity of changing a card for the given player."""
		return self._valid_play_chip(player) and (self.p1_changed == 0 if player == 0 else self.p2_changed == 0)
      
	def make_move(self, move, player, random_seed):
		if move != 13:
			self.round += 1
		# Actual move
		if   move <= 9:
			self._select_card(player, move)
		elif move == 10:
			self._pass(player)
		elif move == 11:
			self._play_chip(player)
		elif move == 12:
			self._play_moon_chip(player)
		elif move == 13:
			self._change_card(player)

		# print(f'next={next_player}, round={self.round[0]}')

		if (move == 13):
			return player # same player goes again if they changed cards
		return 1 - player # switch players

	def _select_card(self, player, card):
		self.played_card_number = card
		self.selected_cards[player] = card

	def _pass(self, player):
		if self.pass_active or self.moon_chip_active:
			self._handle_round_end(player)
		else: self.pass_active = 1

	def _play_chip(self, player):
		if player == 0:
			self.p1_chips -= 1
			self.p1_chips_bet += 1
		else:
			self.p2_chips -= 1
			self.p2_chips_bet += 1
		self.chips_bet_total += 1
		self.pass_active = 0
		self.moon_chip_active = 0

	def _play_moon_chip(self, player):
		self._play_chip(player)  # Perform common chip playing logic
		self.moon_chips_bet_total += 1
		self.moon_chip_active = 1

	def _change_card(self, player):
		if player == 0 and not self.p1_changed:
			self.p1_changed = 1
			self.selected_cards[0] = -1  # Reset selected card for player 1
		elif player == 1 and not self.p2_changed:
			self.p2_changed = 1
			self.selected_cards[1] = -1  # Reset selected card for player 2

		self.played_card_number = -1  # Reset the played card number

	def _handle_round_end(self, player_who_passed_last):
		p1_card = self.selected_cards[0]
		p2_card = self.selected_cards[1]
		p1_diff = abs(self.chips_bet_total - p1_card)
		p2_diff = abs(self.chips_bet_total - p2_card)
		winning_player = -1
		winner_chip_gain = self.chips_bet_total + self.moon_chips_bet_total + 2

		if p1_diff < p2_diff:
			self.p1_chips += winner_chip_gain
			winning_player = 0
		elif p2_diff < p1_diff:
			self.p2_chips += winner_chip_gain
			winning_player = 1
		else:
			if self.moon_chip_active:
				# If a moon chip was played and a pass ends the game, the passing player wins the tie
				if player_who_passed_last == 0: # Player 1 passed last
					self.p1_chips += winner_chip_gain
					winning_player = 0
				else:  # Player 1 passed last
					self.p2_chips += winner_chip_gain
					winning_player = 1
			else:
				# Standard tie-breaking rule
				if player_who_passed_last == 0:  # Player 1 passed last, so Player 2 wins the tie
					self.p2_chips += winner_chip_gain
					winning_player = 0
				else:  # Player 0 passed last, so Player 1 wins the tie
					self.p1_chips += winner_chip_gain
					winning_player = 1

		self._reset_round_state(winning_player)


	def _reset_round_state(self, winning_player):
		self.p1_chips_bet = 0
		self.p2_chips_bet = 0
		self.chips_bet_total = 0
		self.moon_chips_bet_total = 0
		self.pass_active = 0
		self.moon_chip_active = 0
		self.p1_changed = 0
		self.p2_changed = 0
		self.selected_cards[0] = -1
		self.selected_cards[1] = -1
		self.round += 1
		self.start_player = winning_player

	def copy_state(self, state, copy_or_not):
		if self.state is state and not copy_or_not:
			return
		self.state = state.copy() if copy_or_not else state
		self.selected_cards = self.selected_cards.copy()
  
		self.p1_cards = self.state[0:10,:] ###  0-9   self.p1_cards          Cards in the hand of player 1, 0 if the card is in play or in hand, 1 if the card card has been used
		self.p2_cards = self.state[10:20,:] ### 10-19  self.p2_cards          Cards in the hand of player 2, 0 if the card is in play or in hand, 1 if the card card has been used
		self.start_player = self.state[20,:] ###  20    self.start_player      0 or 1, depending on who went first in the current round
		self.pass_active = self.state[21,:] ###  21    self.pass_active	       0 or 1, depending on whether the preceding player passed
		self.p1_changed = self.state[22,:] ###  22    self.p1_changed        0 or 1, 1 after p1 has changed cards in the current round
		self.p2_changed = self.state[23,:] ###  23    self.p2_changed        0 or 1, 1 after p2 has changed cards in the current round
		self.p1_chips = self.state[24,:] ###  24    self.p1_chips          Number of chips in bank for p1
		self.p2_chips = self.state[25,:] ###  25    self.p2_chips          Number of chips in bank for p2
		self.p1_chips_bet = self.state[26,:] ###  26    self.p1_chips_bet      Number of chips bet by p1 in current round
		self.p2_chips_bet = self.state[27,:] ###  27    self.p2_chips_bet      Number of chips bet by p2 in current round
		self.chips_bet_total = self.state[28,:] ###  28    self.chips_bet_total   Number of chips bet in total in current round
		self.moon_chips_bet_total = self.state[29,:] ###  29    self.moon_chips_bet_total    Number of moon chips bet in total in current round
		self.moon_chip_active = self.state[30,:] ###  30    self.moon_chip_active  0 or 1, 1 if the last play was a moon chip
		self.p1_cards_total = self.state[31,:] ###  31    self.p1_cards_total    Number of cards in hand+play for player 1
		self.p2_cards_total = self.state[32,:] ###  32    self.p2_cards_total    Number of cards in hand+play for player 2
		self.p1_nines_total = self.state[33,:] ###  33    self.p1_nines_total    Number of times 9 has been played for player 1
		self.p2_nines_total = self.state[34,:] ###  34    self.p2_nines_total    Number of times 9 has been played for player 2
		self.played_card_number = self.state[35,:] ###  35    self.played_card_number    Card number chosen by the currently active player
		self.round = self.state[36,:]

	def check_end_game(self):
		if (self.p1_chips > 0 and self.p2_chips > 0 and self.p1_cards_total > 2 and self.p2_cards_total > 2):
			return 0
		if (self.p1_chips > self.p2_chips):
			return np.array([1, -1], dtype=np.float32)
		elif (self.p1_chips < self.p2_chips):
			return np.array([-1, 1], dtype=np.float32)
		else: return np.array([-0.1, -0.1], dtype=np.float32)

	# if n=1, transform P0 to Pn, P1 to P0, ... and Pn to Pn-1
	# else do this action n times
	def swap_players(self, player):
		swap_copy = self.selected_cards.copy()
		self.selected_cards = [swap_copy[1], swap_copy[0]]
		
		swap_copy = self.p1_cards.copy()
		self.p1_cards[:] = self.p2_cards[:]
		self.p2_cards[:] = swap_copy[:]
  
		swap_copy = self.p1_changed.copy()
		self.p1_changed[:] = self.p2_changed[:]
		self.p2_changed[:] = swap_copy[:]

		swap_copy = self.p1_chips.copy()
		self.p1_chips[:] = self.p2_chips[:]
		self.p2_chips[:] = swap_copy[:]

		swap_copy = self.p1_chips_bet.copy()
		self.p1_chips_bet[:] = self.p2_chips_bet[:]
		self.p2_chips_bet[:] = swap_copy[:]

		self.start_player[:] = self.start_player.copy() ^ 1  # Flip 0 to 1 and 1 to 0
  
		# self.pass_active = self.state[21,:]
		# self.moon_chip_active = self.state[30,:]
		# self.played_card_number = self.state[35,:]
		self.played_card_number = self.selected_cards[0]
  
		swap_copy = self.p1_cards_total.copy()
		self.p1_cards_total[:] = self.p2_cards_total[:]
		self.p2_cards_total[:] = swap_copy[:]

		swap_copy = self.p1_nines_total.copy()
		self.p1_nines_total[:] = self.p2_nines_total[:]
		self.p2_nines_total[:] = swap_copy[:]


	def get_symmetries(self, policy, valid_actions):
		symmetries = [(self.state.copy(), policy.copy(), valid_actions.copy())]
		return symmetries

	def get_round(self):
		return self.round[0] # TODO: Shouldn't this be a simple number...?
