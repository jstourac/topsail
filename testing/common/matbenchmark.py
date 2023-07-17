import os
import logging

import yaml

from . import env, config, run


def prepare_benchmark_file(path_tpl:str,
                           script_tpl:str,
                           stop_on_error:bool,
                           common_settings:dict,
                           expe_name:str,
                           benchmark_values:dict):

    json_benchmark_file = {}
    json_benchmark_file["--path_tpl"] = path_tpl
    json_benchmark_file["--script_tpl"] = script_tpl
    json_benchmark_file["--remote_mode"] = False
    json_benchmark_file["--stop_on_error"] = stop_on_error
    json_benchmark_file["common_settings"] = common_settings
    json_benchmark_file["expe_to_run"] = [expe_name]


    json_benchmark_file[expe_name] = expe = {}
    expe[expe_name] = benchmark_values

    return json_benchmark_file


def save_benchmark_file(json_benchmark_file, dirname=None, name="benchmark.yaml"):
    if dirname is None:
        dirname = env.ARTIFACT_DIR

    benchmark_file = dirname / name

    logging.info(f"Saving MatrixBenchmarking benchmark file into {benchmark_file} ...")
    with open(benchmark_file, "w") as f:

        yaml.dump(json_benchmark_file, f, default_flow_style=False, sort_keys=False)

    return benchmark_file


def set_benchmark_args(benchmark_file, expe_name, results_dirname=None):
    if results_dirname is None:
        results_dirname = benchmark_file.parent

    args = {}

    args["--workload"] = config.ci_artifacts.get_config("matbench.workload")
    args["--benchmark_file"] = str(benchmark_file)
    args["--results_dirname"] = str(results_dirname)
    args["--expe_to_run"] = expe_name

    return args


def run_benchmark(args):
    logging.info(f"Running MatrixBenchmarking rehearsal with '{args['--benchmark_file']}'...")

    BENCHMARK_CMD_BASE = "matbench benchmark"
    cmd_args = " ".join([f"{k}={v}" for k, v in args.items()])
    cmd = f"{BENCHMARK_CMD_BASE} {cmd_args}"

    with open(env.ARTIFACT_DIR / "benchmark.cmd", "w") as f:
        print(cmd, file =f)

    rehearsal_log_file = env.ARTIFACT_DIR / "benchmark-rehearsal.log"
    test_log_file = env.ARTIFACT_DIR / "benchmark.log"
    try:
        run.run(f"{cmd} 1>'{rehearsal_log_file}' 2>&1")
        logging.info("Rehearsal done.")
    except Exception as e:
        logging.error(f"MatrixBenchmark benchmark rehearsal failed. See '{rehearsal_log_file}' for further detals.")
        return True # failed

    try:
        run.run(f"{cmd} --run 2>&1 | tee -a '{rehearsal_log_file}'")
        logging.info("Benchmark done.")
    except Exception as e:
        logging.error(f"MatrixBenchmark benchmark failed.")
        return True # failed

    return False # didn't fail
