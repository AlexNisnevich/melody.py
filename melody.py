from __future__ import division
from itertools import chain
from random import choice, random, seed
from time import sleep, clock
import os
import math

from pyknon.genmidi import Midi
from pyknon.music import Note, NoteSeq


# melody.py generates simple counterpoint melodies (cantus firmus + first species)
# Requirements:
#	- pyknon (library used to generate midi tracks) - http://kroger.github.com/pyknon/
#	- timidity (utility for playing midi tracks) - http://timidity.sourceforge.net/


# Helpers

def sign(x):
	return math.copysign(1, x)

def remove_dupes(seq):
	# f7 from http://www.peterbe.com/plog/uniqifiers-benchmark
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

# Constants for convenience

KEY_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

P1 = C  = I   = Tonic = Unison = 0
m2 = Db = ii                = 1
M2 = D  = II  = Step        = 2
m3 = Eb = iii               = 3
M3 = E  = III               = 4
P4 = F  = IV                = 5
d5 = Gb = Vo  = Tritone     = 6
P5 = G  = V                 = 7
m6 = Ab = vi                = 8
M6 = A  = VI                = 9
m7 = Bb = vii               = 10
M7 = Bb = VII = LeadingTone = 11
P8      = O   = Octave      = 12

def play_midi(midi):
	midi.write("output.mid")
	os.system("timidity output.mid >/dev/null")

def get_runs_from_melody(melody):
	# e.g.
	# 	input: [0, 2, 4, 2, 0, 7, 5, -3, 2, 0]
	#	output: [[0, 2, 4], [4, 2, 0], [7, 5, -3]]

	runs = []

	for i in range(len(melody) - 2):
		for j in range(i + 2, len(melody)):
			trial_run = melody[i:j+1]
			directions = [sign(trial_run[i+1] - trial_run[i]) for i in range(len(trial_run) - 1)]
			all_directions_equal = (directions.count(directions[0]) == len(directions))
			if all_directions_equal:
				runs.append(tuple(trial_run))
	runs = remove_dupes(runs)

	# remove runs contained in other runs

	contained_runs = []
	for run1 in runs:
		for run2 in runs:
			if run1 != run2 and ''.join(map(str, run2)) in ''.join(map(str, run1)): # run2 contained in run1
				if run2 not in contained_runs:
					contained_runs.append(run2)

	for run in contained_runs:
		runs.remove(run)

	return runs

def check_melody(m, type, verbose = False):
	intervals = [m[i+1] - m[i] for i in range(len(m) - 1)]
	directions = [sign(intervals[i]) for i in range(len(intervals))]
	leaps = [x for x in intervals if abs(x) > Step]
	notes = [x % Octave for x in m]

	def no_repetition():
		if type == 'cantus': # no repetition allowed in cantus firmus
			if 0 not in intervals:
				return True
			else:
				if verbose: print 'fail: no_repetition in cantus firmus: ' + str(m)
		elif type == 'first_species': # one repetition allowed in first species
			if intervals.count(0) <= 1:
				return True
			else:
				if verbose: print 'fail: no_repetition in first species: ' + str(m)

	def no_leaps_larger_than_octave():
		# let's disallow octaves as well, because they rarely sound good
		if not any([abs(x) >= P8 for x in leaps]):
			return True
		else:
			if verbose: print 'fail: no_leaps_larger_than_octave in ' + str(m)

	def no_dissonant_leaps():
		consonant = [M3, P4, P5, m6, P8]
		if not any([abs(x) not in consonant for x in leaps]):
			return True
		else:
			if verbose: print 'fail: no_dissonant_leaps in ' + str(m)

	def between_two_and_four_leaps():
		if len(leaps) in [2, 3, 4]:
			return True
		else:
			if verbose: print 'fail: between_two_and_four_leaps in ' + str(m)

	def has_climax():
		# climax can't be on tonic or leading tone
		climax = max(m)
		position = [i for i, j in enumerate(m) if j == climax][0]
		if climax%Octave not in [Tonic, LeadingTone] and m.count(climax) == 1 and (position + 1) != (len(m) - 1):
			return True
		else:
			if verbose: print 'fail: has_climax in ' + str(m)

	def changes_direction_several_times():
		directional_changes = [intervals[i+1] - intervals[i] for i in range(len(m) - 2)]
		if len([x for x in directional_changes if x < 0]) >= 2:
			return True
		else:
			if verbose: print 'fail: changes_direction_several_times in ' + str(m)

	def no_note_repeated_too_often():
		for note in notes:
			if notes.count(note) > 3:
				if verbose: print 'fail: no_note_repeated_too_often in ' + str(m)
				return False
		return True

	def final_note_approached_by_step():
		if abs(m[-1] - m[-2]) <= Step:
			return True
		else:
			if verbose: print 'fail: final_note_approached_by_step in ' + str(m)

	def larger_leaps_followed_by_change_of_direction():
		for i in range(len(m) - 2):
			if abs(intervals[i]) > 4 and directions[i] == directions[i + 1]:
				if verbose: print 'fail: larger_leaps_followed_by_change_of_direction in ' + str(m)
				return False
		return True

	def leading_note_goes_to_tonic():
		for i in range(len(m) - 1):
			if m[i] %12 == 11 and m[i+1]%12 != 0:
				if verbose: print 'fail: leading_note_goes_to_tonic in ' + str(m)
				return False
		return True

	def no_more_than_two_consecutive_leaps_in_same_direction():
		for i in range(len(m) - 2):
			if abs(intervals[i]) > Step and abs(intervals[i + 1]) > Step and directions[i] == directions[i + 1]:
				if verbose: print 'fail: no_more_than_two_consecutive_leaps_in_same_direction in ' + str(m)
				return False
		return True

	def no_same_two_intervals_in_a_row():
		for i in range(len(m) - 2):
			if intervals[i] > Step and intervals[i] == - intervals[i + 1]:
				if verbose: print 'fail: no_same_two_intervals_in_a_row in ' + str(m)
				return False
		return True

	def no_noodling():
		for i in range(len(m) - 3):
			if intervals[i] == - intervals[i + 1] and intervals[i + 1] == - intervals[i + 2]:
				if verbose: print 'fail: no_noodling in ' + str(m)
				return False
		return True

	def no_long_runs():
		runs = get_runs_from_melody(m)
		for run in runs:
			if len(run) > 4:
				if verbose: print 'fail: no_long_runs in ' + str(m) + ' : ' + str(runs)
				return False
		return True

	def no_unresolved_melodic_tension():
		consonant_movements = [m3, M3, P4, P5, m6, P8]

		runs = get_runs_from_melody(m)
		for run in runs:
			movement = abs(run[0] - run[-1])
			if movement not in consonant_movements:
				if verbose: print 'fail: no_unresolved_melodic_tension in ' + str(m) + ' : ' + str(runs)
				return False
		return True

	def no_sequences():
		triples = [m[i:i+3] for i in range(len(m)-2)]
		normalized_triples = [(0, t[1]-t[0], t[2]-t[0]) for t in triples]

		if len(normalized_triples) == len(set(normalized_triples)): # no duplicates
			return True
		else:
			if verbose: print 'fail: no_sequences in ' + str(m) + ' : ' + str(normalized_triples)
			return False

	return no_note_repeated_too_often() and leading_note_goes_to_tonic() and no_same_two_intervals_in_a_row() and no_repetition() and larger_leaps_followed_by_change_of_direction() and no_dissonant_leaps() and no_leaps_larger_than_octave() and no_noodling() and between_two_and_four_leaps() and has_climax() and final_note_approached_by_step() and no_more_than_two_consecutive_leaps_in_same_direction() and changes_direction_several_times() and no_long_runs() and no_unresolved_melodic_tension() and no_sequences()

def check_first_species(cantus, first_species, verbose = False):
	vertical_intervals = [abs(cantus[i] - first_species[i]) for i in range(len(cantus))]
	v_i = vertical_intervals

	def no_dissonant_intervals():
		consonant = [Unison, m3, M3, P5, m6, M6]
		return not any([(x % Octave) not in consonant for x in vertical_intervals])

	def no_intervals_larger_than_12th():
		return not any([x > (P8 + P5) for x in vertical_intervals])

	def no_parallel_fifths_or_octaves():
		for i in range(len(cantus) - 1):
			if (v_i[i] == P5 and v_i[i+1] == P5) or (v_i[i] == P8 and v_i[i+1] == P8):
				print 'fail: no_parallel_fifths_or_octaves in vertical intervals: ' + str(vertical_intervals)
				return False
		return True

	def no_parallel_chains():
		for i in range(len(cantus) - 1):
			if v_i[i] == v_i[i+1] and v_i[i+1] == v_i[i+2] and v_i[i+2] == v_i[i+3]:
				print 'fail: no_parallel_chains in vertical intervals: ' + str(vertical_intervals)
				return False
		return True

	return no_parallel_fifths_or_octaves() and no_parallel_chains() and no_dissonant_intervals() and no_intervals_larger_than_12th()

def pick_melody(length, start_note = I, cantus = None): # pass cantus if this is a species melody
	registers = {
		'major': [IV-O, V-O, VI-O, VII-O, I, II, III, IV, V, VI, VII, I+O, II+O, III+O, IV+O],
		'minor': [IV-O, V-O, vi-O, vii-O, I, II, iii, IV, V, vi, vii, I+O, II+O, iii+O, IV+O]
	}

	tonality = 'major' # avoiding minor for now
	register = registers[tonality]

	melody = [start_note]
	for i in range(length - 2):
		if cantus:
			allowed_intervals = [Unison, m2, M2, M3, P4, P5, m6, P8]
			allowed_vertical_intervals = [m3, M3, P5, m6, M6]

			# do some optimizing now to pass the first species tests for middle notes
			available_notes = [x for x in register if abs(x - melody[-1]) in allowed_intervals
					and x > cantus[i+1] 											# no cross-over
					and abs(x - cantus[i+1]) % Octave in allowed_vertical_intervals # consonant vertical interval
					and abs(x - cantus[i+1]) < (P8 + P5) 							# no vertical interval larger than 12th
			]

			if len(available_notes) > 0:
				note = choice(available_notes)
			else:
				return False, 'none'
		else:
			allowed_intervals = [m2, M2, M3, P4, P5, m6]

			note = choice([x for x in register if abs(x - melody[-1]) in allowed_intervals])
		melody.append(note)
	melody.append(choice([I, I + Octave]))

	return melody, tonality

def random_transpose(melodies):
	key = choice([C, D, Eb, F, G, A-O, Bb-O])
	return [[x + key for x in melody] for melody in melodies]

def display_melody(melodies, raw_melodies, tonality, time_elapsed, tries):
	def pack_melody(melody, key):
		return str(sum([(x + 12) * pow(24, i) for i, x in enumerate(melody + [key])]))

	key = melodies[0][0] % Octave
	packed_melodies = '-'.join([pack_melody(m, key) for m in raw_melodies])

	print
	print '=== Melody #' + packed_melodies + ' ==='
	print 'Key of ' + KEY_NAMES[key] + ' ' + tonality.capitalize()

	# display each melody in a separate line
	for i in range(len(melodies)):
		print ' '.join([KEY_NAMES[x%Octave] + str(4 + (x+3)//Octave) for x in melodies[i]]) + ' - ' + str(raw_melodies[i])

	# display information about the melody
	vertical_intervals = [abs(cantus[i] - first_species[i]) for i in range(len(cantus))]
	print 'Vertical Intervals: ' + str(vertical_intervals)
	# print 'Runs: ' + str(get_runs_from_melody(raw_melodies[0]))

	# display timing information
	print str(time_elapsed) + ' secs taken (' + ' + '.join(["{:,d}".format(m) for m in tries]) + ' melodies tried)'
	print

def midi_from_melodies(melodies):
	notes = [[Note(x%Octave, 4 + x//Octave, 1/4) for x in melody] for melody in melodies]
	chords = [NoteSeq([melody_notes[i] for melody_notes in notes]) for i in range(len(melody))]

	midi = Midi(tempo=120)
	midi.seq_chords(chords)
	return midi

random_seed = random()
print 'Seed: %.16f' % random_seed
seed(random_seed)

while True:
	melodies = []
	try_again = False

	# start timing
	start_time = clock()
	tries = [0, 0]

	# generate cantus firmus (base melody)
	while True:
		tries[0] += 1
		cantus, tonality = pick_melody(10, Tonic)
		if cantus and check_melody(cantus, 'cantus'):
			break
	melodies.append(cantus)

	# generate first species above cantus firmus
	while True:
		tries[1] += 1
		if tries[1] >= 50000:
			try_again = True
			break

		first_species, tonality = pick_melody(10, choice([P5, Octave]), cantus)
		if first_species and check_melody(first_species, 'first_species') and check_first_species(cantus, first_species):
			break
	if try_again:
		print 'No matching first species found for this cantus firmus: ' + str(cantus)
		print str(clock() - start_time) + ' secs taken (' + ' + '.join(["{:,d}".format(m) for m in tries]) + ' melodies tried)'
		print
		continue
	melodies.append(first_species)

	# finish timing
	time_elapsed = clock() - start_time

	# transpose to random valid key
	transposed_melodies = random_transpose(melodies)

	# display notes and generate midi
	display_melody(transposed_melodies, melodies, tonality, time_elapsed, tries)
	midi = midi_from_melodies(transposed_melodies)
	play_midi(midi)
