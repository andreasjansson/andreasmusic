#!/bin/bash

pushd $(dirname $0)

rm *.{wav,mp3}

for r in 44100 22050
do
    for b in 8 16 24
    do
        for c in 1 2
        do
            for f in 220 440
            do
                name=rate$r-bits$b-channels$c-freq$f-duration1
                sox -n -r$r -b$b -c$c $name.wav synth 1 sin $f
                ffmpeg -i $name.wav $name.mp3
            done
        done
    done
done

popd
