# TODO


fix new scenario error:
mxops execute -n MAIN -s queries scenes/accounts/mainnet.yaml scenes/queries/token_identifiers.yaml 
 -> faire des tests sur les regex
 match n'est peut être pas adapté -> on veut une correspondance exacte, pas une sub string
 
MxOps  Copyright (C) 2023  Catenscia
This program comes with ABSOLUTELY NO WARRANTY
[2023-02-18 10:11:37,953 data INFO] Scenario queries created for network MAIN [data:287 in create_scenario]
[2023-02-18 10:11:37,954 scene INFO] Executing scene scenes/accounts/mainnet.yaml [scene:69 in execute_scene]
Traceback (most recent call last):
  File "/home/etwnn/anaconda3/envs/mxarb_env/bin/mxops", line 8, in <module>
    sys.exit(main())
  File "/mnt/StorageDevice/Documents/Programmation/Catenscia/xOps/mxops/__main__.py", line 54, in main
    execution_cli.execute_cli(args)
  File "/mnt/StorageDevice/Documents/Programmation/Catenscia/xOps/mxops/execution/cli.py", line 65, in execute_cli
    execute_scene(element_path)
  File "/mnt/StorageDevice/Documents/Programmation/Catenscia/xOps/mxops/execution/scene.py", line 87, in execute_scene
    if re.match(scenario_pattern, scenario_data.name) is not None:
  File "/home/etwnn/anaconda3/envs/mxarb_env/lib/python3.8/re.py", line 191, in match
    return _compile(pattern, flags).match(string)
  File "/home/etwnn/anaconda3/envs/mxarb_env/lib/python3.8/re.py", line 304, in _compile
    p = sre_compile.compile(pattern, flags)
  File "/home/etwnn/anaconda3/envs/mxarb_env/lib/python3.8/sre_compile.py", line 764, in compile
    p = sre_parse.parse(p, flags)
  File "/home/etwnn/anaconda3/envs/mxarb_env/lib/python3.8/sre_parse.py", line 948, in parse
    p = _parse_sub(source, state, flags & SRE_FLAG_VERBOSE, 0)
  File "/home/etwnn/anaconda3/envs/mxarb_env/lib/python3.8/sre_parse.py", line 443, in _parse_sub
    itemsappend(_parse(source, state, verbose, nested + 1,
  File "/home/etwnn/anaconda3/envs/mxarb_env/lib/python3.8/sre_parse.py", line 668, in _parse
    raise source.error("nothing to repeat",
re.error: nothing to repeat at position 0
