source .venv/bin/activate
export EXPERIMENT_NAME=afltest
PYTHONPATH=. python experiment/run_experiment.py \
	--experiment-config experiment-config.yaml \
	--benchmarks libpcap_fuzz_both \
	--experiment-name test1 \
	--fuzzers afl_2_52_b my_fuzz

