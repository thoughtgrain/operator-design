cd /home/claude/operator-design/screens/drill/frames && python3 build.py > /dev/null && rm -rf _p && mkdir -p _p && for i in 1 2 3 4; do c=$(echo ratio teeth wear bite | cut -d' ' -f$i); for v in 0 50 100; do cp $c-$v.svg _p/c$i-$(printf %03d $v).svg; done; done && cp rest.svg _p/ && python3 -c "
import build
from pathlib import Path
s=build.frame(build.DEFAULTS, 2.3); s.write(Path('_p/playing.svg'),'playing',build.header_values(build.DEFAULTS))
" && cd ../../.. && python3 opxy/tools/perceptibility.py screens/drill/frames/_p --scores 5,4,3,5 --names ratio,teeth,wear,bite; python3 opxy/tools/lint_frame.py screens/drill/frames/rest.svg screens/drill/frames/{ratio,teeth,wear,bite}-{0,50,100}.svg 2>&1 | tail -1
