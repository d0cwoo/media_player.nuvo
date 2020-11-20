# media_player.nuvo
Media player for Nuvo Grand Concerto and Essentia E6G system whole-house distribution system

Interested in emulating Nuvo keypads as the OLED are fading and unreadable. Replacement keypads are unavailable

Instead of using the pynuvo (which uses the wrong Baud rate for Grand Concerto and Essentia https://pypi.org/project/pynuvo/). Created a new file named pynuvo3. 
pynuvo3 incorporates other integration for similar multizone controller amplifier already in the Home Assistant core, namely "Monoprice 6-zone Amplifier" and "Monoprice Blackbird Matrix Switch" 

https://github.com/home-assistant/core/tree/dev/homeassistant/components/monoprice

https://github.com/home-assistant/core/tree/dev/homeassistant/components/blackbird


# Manual install
1. Download and unzip the repo archive. (You could also click "Download ZIP" after pressing the green button in the repo, alternatively, you could clone the repo from SSH add-on).
2. Copy contents of the archive/repo into your /config directory.
3. Restart your Home Assistant.
