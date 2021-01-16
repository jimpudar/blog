Title: Apple II Monitor on Modern Mac Pro
Date: 2020-06-11
Category: Technology
Tags: composite, video, monitor, apple, hardware
Slug: apple-ii-monitor
Author: Jim Pudar
Summary: Adventures in connecting an Apple II Monitor to a modern Mac Pro
Status: draft

Back when I was living in Silicon Valley, I bought an old Apple II monitor
from a local seller. It's a very pretty monochrome green phosphor CRT that
worked properly when I bought it.

Somewhere along the move from California back to Ann Arbor, MI, the monitor
stopped working - much to my dismay, it no longer turns on.

This post will chronicle my attempt to repair it and use it as a secondary
monitor for my Mac Pro (2019).

# Test Rig

The Apple II monitor requires a composite video input. This is fed via an RCA
jack, similar to the late model North American Nintendo Entertainment System.
Since this format is not typically available on modern computers, I turned to
the Raspberry Pi system. Since these are meant to be usable even in third
world countries where the latest monitor technology may not be available, a
hidden composite out connection is present in the audio jack.

I soldered a cable using the appropriate connectors and a piece of high
quality coax.

In order to use the composite out on the Raspberry Pi 4, I need to do a bit of
configuration on the device. See
[the documentation](https://www.raspberrypi.org/documentation/configuration/config-txt/video.md)
for more information on this process.

In my case, in the `config.txt` file, I need to set `enable_tvout=1`. I've
also opted to set `sdtv_disable_colourburst=1` to use native monochrome output
to hopefully get a sharper image.

Now that the configuration is complete, I can test the device using my TV.
