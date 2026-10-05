#!/usr/bin/env bash
# Usage:  bash install.sh            (default PyPI)
#         bash install.sh mirror     (Tsinghua PyPI mirror, for slow / blocked connections)
set -e
PIP_OPTS="--timeout 120 --retries 10"
if [ "$1" = "mirror" ]; then
  PIP_OPTS="$PIP_OPTS -i https://pypi.tuna.tsinghua.edu.cn/simple"
fi
python -m pip install $PIP_OPTS --upgrade pip
python -m pip install $PIP_OPTS -r requirements.txt
python -m pip install $PIP_OPTS --no-deps csdid==0.4.2 drdid==1.1.6
python - <<'PY'
import sys, numpy, pandas, scipy, matplotlib, statsmodels, linearmodels
from csdid.att_gt import ATTgt
print("Python", sys.version.split()[0], "| numpy", numpy.__version__, "| pandas", pandas.__version__,
      "| linearmodels", linearmodels.__version__, "| csdid OK")
PY
