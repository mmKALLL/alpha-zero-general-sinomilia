#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess

import coloredlogs

from Coach import Coach

log = logging.getLogger(__name__)
coloredlogs.install(level='INFO')  # Change this to DEBUG to see more info.


def run(args):
	from GameSwitcher import import_game
	Game, NNet, players, NUMBER_PLAYERS = import_game(args.game)

	log.debug('Loading %s...', Game.__name__)
	g = Game()

	log.debug('Loading %s...', NNet.__name__)
	nn_args = dict(
		lr=args.learn_rate,
		dropout=args.dropout,
		epochs=args.epochs,
		batch_size=args.batch_size,
		nn_version=args.nn_version,
		learn_rate=args.learn_rate,
		no_compression=args.no_compression,
		q_weight=args.q_weight,
	)
	nnet = NNet(g, nn_args)

	if args.load_model:
		log.info('Loading checkpoint "%s"...', args.load_folder_file)
		nnet.load_checkpoint(os.path.dirname(args.load_folder_file), os.path.basename(args.load_folder_file))
		if not args.useray:
			compare_settings(args)
	# else:
	# 	log.warning('Not loading a checkpoint!')

	log.debug('Loading the Coach...')
	c = Coach(g, nnet, args)

	if args.load_model and not args.forget_examples:
		log.info("Loading 'trainExamples' from file...")
		c.loadTrainExamples()

	if not args.useray:
		# Backup code used for this run
		subprocess.run(f'mkdir -p "{args.checkpoint}/"', shell=True)
		subprocess.run(f'cp *py santorini/*py "{args.checkpoint}/"', shell=True)
		subprocess.run(
			f'[ -f "{args.checkpoint}/settings.txt" ] && mv "{args.checkpoint}/settings.txt" "{args.checkpoint}/settings."`date +%s` ;   echo "{args}" > "{args.checkpoint}/settings.txt"',
			shell=True)

	log.debug('Starting the learning process 🎉')
	c.learn()


# Compare current settings and settings of checkpoints, display main differences
def compare_settings(args):
	settings_file = os.path.join(os.path.dirname(args.load_folder_file), 'settings.txt')

	# Load settings
	if not os.path.isfile(settings_file):
		return
	with open(settings_file, 'r') as f:
		previous_args = f.read()

	# Compute differences on dict versions
	previous_args_dict, current_args_dict = vars(eval('argparse.' + previous_args)), vars(args)
	changed_keys = set([k for k in set(list(previous_args_dict.keys()) + list(current_args_dict.keys())) if
	                    previous_args_dict.get(k) != current_args_dict.get(k)])
	for key in ['load_folder_file', 'checkpoint', 'numIters', 'arenaCompare', 'maxlenOfQueue', 'load_model']:
		changed_keys.discard(key)

	if changed_keys:
		log.info('Some option(s) changed compared to loaded checkpoint:')
		for k in changed_keys:
			print(f'{k}: {previous_args_dict.get(k)} --> {current_args_dict.get(k)}')


def profiling(args):
	import cProfile, pstats
	profiler = cProfile.Profile()
	# import yappi
	args.parallel_inferences, args.numIters, args.numEps, args.epochs = 1, 1, 8, 1  # warmup run
	run(args)

	print('\nstart profiling')
	args.parallel_inferences, args.numIters, args.numEps, args.epochs = 1, 1, 8, 1
	# Core of the training
	# yappi.start()
	profiler.enable()
	run(args)
	# yappi.stop()
	profiler.disable()

	# debrief
	profiler.dump_stats('execution.prof')
	print('check dumped stats in execution.prof')
	# Sample code:
	# from pstats import Stats, SortKey
	# p = Stats('execution.prof')
	# p.strip_dirs().sort_stats('cumtime').print_stats(20)
	# p.strip_dirs().sort_stats('tottime').print_stats(10)

	# threads = yappi.get_thread_stats()
	# for thread in threads:
	# 	print("Function stats for (%s) (%d)" % (thread.name, thread.id))  # it is the Thread.__class__.__name__
	# 	yappi.get_func_stats(ctx_id=thread.id).print_all()

	breakpoint()

def main():
	parser = argparse.ArgumentParser(description='tester')
	parser.add_argument('game'                     , action='store', default='sinomilia', help='The name of the game to simulate')
	parser.add_argument('--checkpoint'      , '-C' , action='store', default='./temp/', help='')
	parser.add_argument('--load-folder-file', '-L' , action='store', default=None     , help='')
	
	parser.add_argument('--numEps'          , '-e' , action='store', default=500  , type=int  , help='Number of complete self-play games to simulate during a new iteration')
	parser.add_argument('--numItersHistory' , '-i' , action='store', default=5   , type=int  , help='')

	parser.add_argument('--numMCTSSims'     , '-m' , action='store', default=1600 , type=int  , help='Number of moves for MCTS to simulate in FULL exploration')
	parser.add_argument('--tempThreshold'   , '-T' , action='store', default=10   , type=int  , help='Nb of moves after which changing temperature')
	parser.add_argument('--temperature'     , '-t' , action='store', default=[1.25, 0.8], type=float, nargs=2, help='Softmax temp: 1 = to apply before MCTS, 3 = after MCTS, only used for selection not for learning')
	parser.add_argument('--cpuct'           , '-c' , action='store', default=1.25 , type=float, help='cpuct value')
	parser.add_argument('--dirichletAlpha'  , '-d' , action='store', default=-1   , type=float, help='α=0.3 for chess, scaled in inverse proportion to the approximate number of legal moves in a typical position. 0 to disable. -1 for auto.')
	parser.add_argument('--fpu'             , '-f' , action='store', default=0.   , type=float, help='Value for FPU (first play urgency): negative value for absolute value, positive value for parent-based reduction')
	parser.add_argument('--forced-playouts' , '-F' , action='store_true', help='Enabled forced playouts')
	
	parser.add_argument('--learn-rate'      , '-l' , action='store', default=0.0003, type=float, help='')
	parser.add_argument('--epochs'          , '-p' , action='store', default=2    , type=int  , help='')
	parser.add_argument('--batch-size'      , '-b' , action='store', default=32   , type=int  , help='')
	parser.add_argument('--dropout'         , '-D' , action='store', default=0.   , type=float  , help='')
	parser.add_argument('--nn-version'      , '-V' , action='store', default=1    , type=int  , help='Which architecture to choose')

	### Advanced params ###
	parser.add_argument('--q-weight'        , '-q' , action='store', default=0.5  , type=float, help='Weight for mixing Q into value loss')
	parser.add_argument('--updateThreshold'        , action='store', default=0.60 , type=float, help='During arena playoff, new neural net will be accepted if threshold or more of games are won')
	parser.add_argument('--ratio-fullMCTS'         , action='store', default=5    , type=int  , help='Ratio of MCTS sims between full and fast exploration')
	parser.add_argument('--prob-fullMCTS'          , action='store', default=0.25 , type=float, help='Probability to choose full MCTS exploration')
	parser.add_argument('--universes'       , '-u' , action='store', default=1    , type=int  , choices=range(9), help='Number of universes (up to 8); will switch between each of them at each rollout. Set to 0 for a deterministic exploration')

	parser.add_argument('--forget-examples'        , action='store_true', help='Do not load previous examples')
	parser.add_argument('--numIters'        , '-n' , action='store', default=50   , type=int, help='')
	parser.add_argument('--stop-after-N-fail', '-s', action='store', default=-1   , type=float, help='Number of consecutive failed arenas that will trigger process stop (-N means N*numItersHistory)')
	parser.add_argument('--profile'                , action='store_true', help='profiler')
	parser.add_argument('--debug'                  , action='store_true', help='Disable all optimisations to allow easier debugging')
	parser.add_argument('--useray'                 , action='store_true', help='Mode for "ray", disable some messages')
	parser.add_argument('--parallel-inferences','-P',action='store', default=8    , type=int  , help='Size of batch for inferences = nb of threads, set to 1 to disable')
	parser.add_argument('--no-compression'         , action='store_true', help='Prevent using in-memory data compression (huge memory decrease and impact by only by ~1 second per 100k samples), useful for easier debugging')
	parser.add_argument('--no-mem-optim'           , action='store_true', help='Prevent cleaning MCTS tree of old moves during each game')
	
	args = parser.parse_args()
	args.arenaCompare = 30
	args.maxlenOfQueue = int(2.5e6 / ((
		                                  2 if args.no_compression else 0.5) * args.numItersHistory))  # at most 2GB per process, with each example weighing 2kB (or 0.5kB)
	if args.stop_after_N_fail < 0:
		args.stop_after_N_fail = -args.stop_after_N_fail * args.numItersHistory

	if args.debug:
		args.parallel_inferences = 1
		args.no_compression = True
		args.no_mem_optim = True

	if args.useray and args.updateThreshold == 0.60:
		args.updateThreshold == 0.55

	args.load_model = (args.load_folder_file is not None)
	if args.profile:
		profiling(args)
	else:
		if not args.useray:
			print(args)
		run(args)


if __name__ == "__main__":
	main()
