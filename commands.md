# To compile definition files into a single network file
```
netconvert --node-files=sumo_files/intersection.nod.xml --edge-files=sumo_files/intersection.edg.xml -o sumo_files/intersection.net.xml --lefthand
```
intersection.net.xml is generated

# To view/check the network
```
sumo-gui -c sumo_files/intersection.sumocfg
```
# To generate random traffic, route direction
```
python "%SUMO_HOME%/tools/randomTrips.py" -n sumo_files/intersection.net.xml -r sumo_files/intersection.rou.xml -e 3600 -p 3.0 --validate
```