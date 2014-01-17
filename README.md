melody.py
=========

**melody.py** generates random 10-note [first species counterpoint](http://en.wikipedia.org/wiki/Counterpoint#First_species) melodies by first finding a random *cantus firmus* melody that matches a set of heuristics and then finding an appropriate counterpoint melody. A total of [16 heuristics](https://github.com/AlexNisnevich/melody.py/blob/master/melody.py#L81-L212) are used for each individual melody and [4 heuristics](https://github.com/AlexNisnevich/melody.py/blob/master/melody.py#L214-L239) are used to match two melodies in counterpoint. Results are outputted as MIDI files using Pyknon and then played using Timidity.
