const MODE=window.PHASMO_MODE||'control';
const params=new URLSearchParams(location.search);
function normalizeRoomKey(raw){let v=(raw||'default').toLowerCase().trim().replace(/[^a-z0-9_-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,64);return v||'default'}
const room=normalizeRoomKey(params.get('room')||'default');
function roomCodeKeyFor(targetRoom){return `phasmoRoomCode:${normalizeRoomKey(targetRoom||room)}`}
function cleanRoomCode(raw){return (raw||'').replace(/[^0-9]/g,'').slice(0,4)}
let roomCode=cleanRoomCode(params.get('code')||localStorage.getItem(roomCodeKeyFor(room))||'');
if(roomCode.length===4){ localStorage.setItem(roomCodeKeyFor(room), roomCode); }
const API='/api/phasmo';
let authPromptActive=false;
let lastSyncAt=0;
function storedRoomCodeFor(targetRoom){const key=roomCodeKeyFor(targetRoom); const fallback=normalizeRoomKey(targetRoom)===room?roomCode:''; return cleanRoomCode(localStorage.getItem(key)||fallback||'')}
function codeSuffixFor(targetRoom=room){const code=storedRoomCodeFor(targetRoom);return code&&code.length===4?'&code='+encodeURIComponent(code):''}
function codeSuffix(){return codeSuffixFor(room)}
function rememberRoomCodeFor(targetRoom,raw){const cleaned=cleanRoomCode(raw); const key=roomCodeKeyFor(targetRoom); if(cleaned.length===4){localStorage.setItem(key,cleaned); if(normalizeRoomKey(targetRoom)===room)roomCode=cleaned;} return cleaned;}
function rememberRoomCode(raw){return rememberRoomCodeFor(room,raw)}
async function retryWithRoomCode(message,targetRoom=room){if(authPromptActive)return false; authPromptActive=true; try{const entered=prompt(message||'This room is locked. Enter the 4-digit room passcode.'); return rememberRoomCodeFor(targetRoom,entered).length===4;} finally{authPromptActive=false;}}
const E=['dots','emf5','freezing','orbs','writing','box','uv'];
const EL={dots:'D.O.T.S Projector',emf5:'EMF Level 5',freezing:'Freezing Temperatures',orbs:'Ghost Orb',writing:'Ghost Writing',box:'Spirit Box',uv:'Ultraviolet'};
const G=[
['Aswang',['freezing','writing','dots']],['Banshee',['dots','orbs','uv']],['Dayan',['emf5','orbs','box']],['Demon',['writing','uv','freezing']],['Deogen',['dots','writing','box']],['Gallu',['emf5','box','uv']],['Goryo',['dots','emf5','uv']],['Hantu',['orbs','uv','freezing']],['Jinn',['emf5','uv','freezing']],['Kormos',['orbs','box','uv']],['Mare',['writing','orbs','box']],['Moroi',['writing','freezing','box']],['Myling',['writing','emf5','uv']],['Obake',['emf5','orbs','uv']],['Obambo',['uv','writing','dots']],['Oni',['dots','emf5','freezing']],['Onryo',['orbs','freezing','box']],['Phantom',['dots','uv','box']],['Poltergeist',['writing','uv','box']],['Raiju',['dots','emf5','orbs']],['Revenant',['writing','orbs','freezing']],['Shade',['writing','emf5','freezing']],['Spirit',['writing','emf5','box']],['Thaye',['dots','writing','orbs']],['The Mimic',['uv','freezing','box']],['The Twins',['emf5','freezing','box']],['Wraith',['dots','emf5','box']],['Yokai',['dots','orbs','box']],['Yurei',['dots','orbs','freezing']]
].map(([name,ev])=>({name,ev}));
G.push({name:'Deildegast',ev:['emf5','writing','dots']});
const GENDER_RULES={Banshee:'female',Dayan:'female',Krampus:'male'};
const HUNT_RULES={Demon:{threshold:70,any:true,note:'Demon can use an ability above normal thresholds.'},Yokai:{threshold:80,note:'Only with voice activity nearby.'},Thaye:{threshold:75,note:'Young Thaye; threshold falls as it ages.'},Raiju:{threshold:65,note:'Near active electronics.'},Dayan:{threshold:65,note:'When players are moving.'},Obambo:{threshold:65,note:'Aggressive state.'},Mare:{threshold:60,note:'In darkness; lower when lights are on.'},Onryo:{threshold:60,any:true,note:'Can hunt after flame/candle mechanics.'},Deogen:{threshold:40,note:'Late hunter.'},Shade:{threshold:35,note:'Very low threshold.'}};
const DEFAULT_HUNT_THRESHOLD=50;
const CURSED_ITEMS=['Music Box','Ouija Board','Tarot Cards','Summoning Circle','Haunted Mirror','Monkey Paw','Voodoo Doll'];
const CURSED_USE={
 'Music Box':'Use it to locate the ghost by song/humming. Risk: dropping it, reaching the ghost, or running out of sanity can trigger a cursed hunt.',
 'Ouija Board':'Ask location, age, sanity, etc. Always say goodbye. Low sanity or unsafe questions can break the board and trigger a cursed hunt.',
 'Tarot Cards':'Draw one card at a time for random effects. High variance; Death starts a cursed hunt, Hanged Man can kill.',
 'Summoning Circle':'Light all candles to force a manifestation/photo opportunity. The ghost will usually transition into a cursed hunt shortly after.',
 'Haunted Mirror':'Look through it to identify the favorite room. It drains sanity while used and can break/start a cursed hunt.',
 'Monkey Paw':'Grants wishes with tradeoffs. Strong utility, but several wishes can create major danger or cursed-hunt situations.',
 'Voodoo Doll':'Push pins to force interactions. The heart pin starts a cursed hunt, and low sanity can force all pins.'
};
const CURSED_LOCATIONS={
 "6 Tanglewood Drive": {
  "Music Box": "Nursery / purple baby room shelf by the light switch.",
  "Ouija Board": "Back of basement, on a small table.",
  "Tarot Cards": "Living room / foyer corner by the couch, on a side table.",
  "Summoning Circle": "Basement, immediately at the bottom of the stairs.",
  "Haunted Mirror": "Living-room hall alcove outside the master bedroom door, on the wall.",
  "Monkey Paw": "Garage, sitting on/near the garbage bin in the corner.",
  "Voodoo Doll": "Garage corner, sitting on a garbage bin."
 },
 "42 Edgefield Road": {
  "Music Box": "First room on the left, small table next to a lamp.",
  "Ouija Board": "Kitchen-back laundry room, under shelves.",
  "Tarot Cards": "By front door, on a small table next to the key bowl.",
  "Summoning Circle": "Back of basement, next to the possible fuse box location.",
  "Haunted Mirror": "By front door, at the base of the stairs on the wall.",
  "Monkey Paw": "Upstairs kid/orange bedroom, on the baby changing table.",
  "Voodoo Doll": "Upstairs blue bedroom, on top of the bed."
 },
 "10 Ridgeview Court": {
  "Music Box": "Upstairs purple bedroom, small table by the door.",
  "Ouija Board": "Down the left hall, laundry room shelves.",
  "Tarot Cards": "By front door, on a small table next to the key bowl.",
  "Summoning Circle": "Basement, in the middle at the bottom of the staircase.",
  "Haunted Mirror": "Across from the basement staircase, on the wall.",
  "Monkey Paw": "Upstairs blue/teal bedroom, on the desk.",
  "Voodoo Doll": "Bench next to the piano."
 },
 "13 Willow Street": {
  "Music Box": "Next to the front door, on a small table.",
  "Ouija Board": "Laundry room off garage, on the washing machine.",
  "Tarot Cards": "Living room / foyer side table next to the couch.",
  "Summoning Circle": "Basement, on the 90-degree turn.",
  "Haunted Mirror": "Laundry room off garage, on the ground in the left corner.",
  "Monkey Paw": "Dining room glass display cabinet, on a shelf.",
  "Voodoo Doll": "Blue bedroom glass display cabinet; open the cabinet door."
 },
 "Grafton Farmhouse": {
  "Music Box": "Second floor small bedroom, on an end table by the bed.",
  "Ouija Board": "Third floor attic, on the ground near boxes / standing lamp.",
  "Tarot Cards": "First floor library, on the desk.",
  "Summoning Circle": "Second floor doll room, on the ground.",
  "Haunted Mirror": "Second floor master bedroom, on a table.",
  "Monkey Paw": "First floor dining room, on a side table.",
  "Voodoo Doll": "First floor seamstress/work room, on a table."
 },
 "Bleasdale Farmhouse": {
  "Music Box": "Tea room / left-hand room immediately after entering, on the china cabinet or shelf.",
  "Ouija Board": "Living room, propped on the floor against a couch.",
  "Tarot Cards": "Attic bedroom / crystal-ball room, on the table.",
  "Summoning Circle": "Utility / storage room, near the back corner.",
  "Haunted Mirror": "Trophy room / display room, on the floor near a cabinet.",
  "Monkey Paw": "Second-floor study, on the shelf behind the chair.",
  "Voodoo Doll": "Second-floor bedroom, on the seat/bench at the end of the bed."
 },
 "Camp Woodwind": {
  "Music Box": "Inside yellow tent on the left side, small table by the entrance.",
  "Ouija Board": "Right of fire pit, on the folding tables.",
  "Tarot Cards": "Left of front gate, on the second picnic table.",
  "Summoning Circle": "Straight back from the truck, by folding activity tables.",
  "Haunted Mirror": "Middle of map, base of the string-light tree.",
  "Monkey Paw": "Back curved path, on a wooden table.",
  "Voodoo Doll": "Left of bathrooms, near the red and teal tents."
 },
 "Brownstone High School": {
  "Music Box": "Entry lobby, sitting on the right-side second bench.",
  "Ouija Board": "Entry lobby, on the ground behind the left pillar.",
  "Tarot Cards": "Entry lobby, second bench on the left side.",
  "Summoning Circle": "Entry lobby, straight back by the wet floor sign.",
  "Haunted Mirror": "Entry lobby, leaning against the back of the right pillar.",
  "Monkey Paw": "Entry lobby, on a box against the front of the right pillar.",
  "Voodoo Doll": "Entry lobby, straight back on a bench by the wet floor sign."
 },
 "Prison": {
  "Music Box": "Main entry room, immediately inside on the left table in the black bin/tub.",
  "Ouija Board": "Immediate left corner of first room, behind the table with other spawns.",
  "Tarot Cards": "Immediately inside front door, left table in a white bin/tub.",
  "Summoning Circle": "Straight back from front door, back of first room.",
  "Haunted Mirror": "Main lobby, under center-right row of chairs farther into the room.",
  "Monkey Paw": "Immediately inside front door, left table by the metal detector.",
  "Voodoo Doll": "Main entry room, immediately inside on the left table in the open."
 },
 "Sunny Meadows Mental Institution": {
  "Music Box": "Chapel stage area, in one of the circle slots.",
  "Ouija Board": "Chapel stage area, in one of the circle slots.",
  "Tarot Cards": "Chapel stage area, in one of the circle slots.",
  "Summoning Circle": "Chapel stage itself; the circle is on the stage.",
  "Haunted Mirror": "Chapel stage area, in one of the circle slots.",
  "Monkey Paw": "Chapel stage, at the base of the cross near the circle.",
  "Voodoo Doll": "Chapel stage area, in one of the circle slots."
 },
 "Sunny Meadows Restricted": {
  "Music Box": "Chapel stage area, in one of the circle slots.",
  "Ouija Board": "Chapel stage area, in one of the circle slots.",
  "Tarot Cards": "Chapel stage area, in one of the circle slots.",
  "Summoning Circle": "Chapel stage itself; the circle is on the stage.",
  "Haunted Mirror": "Chapel stage area, in one of the circle slots.",
  "Monkey Paw": "Chapel stage, at the base of the cross near the circle.",
  "Voodoo Doll": "Chapel stage area, in one of the circle slots."
 },
 "Maple Lodge Campsite": {
  "Music Box": "Campfire by the totem pole, sitting on a stump through reception.",
  "Ouija Board": "Back-left restroom building alley/hallway shelf.",
  "Tarot Cards": "First picnic table outside the cabin by the lake.",
  "Summoning Circle": "First floor of lake cabin, base of staircase; cabin key is under welcome mat.",
  "Haunted Mirror": "Immediate left side of reception building, above a couch.",
  "Monkey Paw": "Right-hand area off spawn, past wood chopping, on barrel across from porta-potty.",
  "Voodoo Doll": "Left campsite from spawn, by logs around the campfire."
 },
 "Point Hope": {
  "Music Box": "Master bedroom near the top of the lighthouse.",
  "Ouija Board": "Living room area, tucked away on a shelf.",
  "Tarot Cards": "First room on the right / lower living area table.",
  "Summoning Circle": "Upper bathroom floor near the top of the lighthouse.",
  "Haunted Mirror": "Dining room, against a cupboard / cabinet.",
  "Monkey Paw": "Workshop near the top of the lighthouse.",
  "Voodoo Doll": "Kids bedroom, near the window."
 },
 "Nell's Diner": {
  "Music Box": "Manager's Office, next to the coffee machine.",
  "Ouija Board": "Storage room opposite the staff bathroom / employee-only section.",
  "Tarot Cards": "Counter area, behind the counter next to the till.",
  "Summoning Circle": "Men's Bathroom, on the floor.",
  "Haunted Mirror": "Staff room / break room, on a chair next to the vending machine.",
  "Monkey Paw": "Kitchen, on the chopping board / countertop.",
  "Voodoo Doll": "Dining Area, by a table at the back / far-left booth seat."
 }
};
const CURSED_HINTS={
 "6 Tanglewood Drive": "Small house sweep: nursery, garage, basement, dining display, living-room side table.",
 "42 Edgefield Road": "Three-floor sweep: entry/stairs, basement, orange/blue bedrooms, laundry.",
 "10 Ridgeview Court": "Check upstairs bedrooms, piano bench, basement stairs, laundry, and entry table.",
 "13 Willow Street": "Small house sweep: entry table, blue bedroom cabinet, garage laundry, basement turn.",
 "Grafton Farmhouse": "Reworked farmhouse sweep: dining/library/work room on first floor; bedrooms/doll room on second; attic for Ouija.",
 "Bleasdale Farmhouse": "Reworked farmhouse sweep: tea room, living room, utility/storage, trophy room, second-floor study/bedroom, attic crystal room.",
 "Camp Woodwind": "Outdoor sweep: tents, firepit, string-light tree, activity tables, picnic tables.",
 "Brownstone High School": "Large map shortcut: all cursed items are in the entry lobby near benches/pillars/wet floor sign.",
 "Brownstone High School Restricted": "Medium restricted variant; the playable section is randomly assigned when the contract loads.",
 "Prison": "Large map shortcut: all cursed items are in the main entry room/lobby near the left table, chairs, and metal detector.",
 "Prison Restricted": "Small restricted variant; the playable section is randomly assigned when the contract loads.",
 "Sunny Meadows Mental Institution": "Large map shortcut: chapel stage. Most items are in circle slots; Monkey Paw is by the cross.",
 "Sunny Meadows Restricted": "Large map shortcut: chapel stage. Same cursed-item area as full Sunny Meadows.",
 "Maple Lodge Campsite": "New Maple Lodge sweep: reception/campfire, restroom alley, lake cabin, picnic table, barrel/porta-potty area.",
 "Point Hope": "Lighthouse sweep: lower living/dining first, then bedrooms/bathroom/workshop toward the top.",
 "Point Hope Restricted": "Small restricted route; the playable lighthouse area extends through the Dining Room.",
 "Nell's Diner": "Diner sweep: counter, manager office, staff/break room, storage, men's bathroom, dining area, kitchen."
};
const B=[{"id":"hantu-temperature-speed","cat":"Movement Speed","label":"Speed changes with room temperature","up":["Hantu"],"down":[],"w":48,"rel":"High"},{"id":"raiju-electronics-speed","cat":"Movement Speed","label":"Speeds up near active electronics","up":["Raiju"],"down":[],"w":48,"rel":"High"},{"id":"revenant-los-speed","cat":"Movement Speed","label":"Slow searching, extremely fast after detecting a player","up":["Revenant"],"down":[],"w":52,"rel":"High"},{"id":"deogen-distance-speed","cat":"Movement Speed","label":"Very fast far away, very slow when close","up":["Deogen"],"down":[],"w":56,"rel":"High"},{"id":"dayan-moving-speed","cat":"Movement Speed","label":"Fast when a nearby player is moving","up":["Dayan"],"down":[],"w":44,"rel":"High"},{"id":"dayan-still-slow","cat":"Movement Speed","label":"Slow when nearby player stands still","up":["Dayan"],"down":[],"w":40,"rel":"High"},{"id":"twins-speed-profiles","cat":"Movement Speed","label":"Two different hunt speed profiles","up":["The Twins"],"down":[],"w":38,"rel":"Med"},{"id":"thaye-aging-speed","cat":"Movement Speed","label":"Starts fast/hyperactive, calms and slows over time","up":["Thaye"],"down":[],"w":44,"rel":"High"},{"id":"obambo-state-speed","cat":"Movement Speed","label":"Alternates calm/aggressive speed and hunt behavior","up":["Obambo"],"down":[],"w":40,"rel":"Med"},{"id":"aswang-los-ramp","cat":"Movement Speed","label":"Lower base speed but faster line-of-sight acceleration","up":["Aswang"],"down":[],"w":34,"rel":"Med"},{"id":"wraith-no-salt","cat":"Salt / Ultraviolet","label":"Does not disturb salt at all","up":["Wraith"],"down":[],"w":58,"rel":"High"},{"id":"salt-footprints","cat":"Salt / Ultraviolet","label":"Salt disturbed and UV footprints appear","up":[],"down":["Wraith"],"w":45,"rel":"High"},{"id":"gallu-no-salt-enraged","cat":"Salt / Ultraviolet","label":"Cannot disturb salt while enraged","up":["Gallu"],"down":[],"w":36,"rel":"Med"},{"id":"obake-unique-print","cat":"Salt / Ultraviolet","label":"Unique UV print such as six fingers or double switch print","up":["Obake"],"down":[],"w":58,"rel":"High"},{"id":"obake-hides-prints","cat":"Salt / Ultraviolet","label":"Repeated valid UV interactions sometimes leave no print","up":["Obake"],"down":[],"w":32,"rel":"Med"},{"id":"breaker-off-direct","cat":"Electricity / Breaker / Lights","label":"Ghost turns breaker off directly","up":["Hantu","Mare"],"down":["Jinn"],"w":30,"rel":"Med"},{"id":"breaker-on-benefit","cat":"Electricity / Breaker / Lights","label":"Performs better with breaker on","up":["Jinn","Raiju"],"down":["Hantu"],"w":22,"rel":"Low"},{"id":"jinn-breaker-speed","cat":"Electricity / Breaker / Lights","label":"Fast with breaker on, line of sight, and target over 3m away","up":["Jinn"],"down":[],"w":46,"rel":"High"},{"id":"jinn-sanity-drain","cat":"Electricity / Breaker / Lights","label":"Nearby sanity drain with EMF at fuse box","up":["Jinn"],"down":[],"w":38,"rel":"Med"},{"id":"hantu-breath-breaker-off","cat":"Electricity / Breaker / Lights","label":"Freezing breath during hunts when breaker is off or broken","up":["Hantu"],"down":[],"w":48,"rel":"High"},{"id":"mare-lights-off","cat":"Electricity / Breaker / Lights","label":"More dangerous when current room lights are off or broken","up":["Mare"],"down":[],"w":32,"rel":"Med"},{"id":"mare-no-lights-on","cat":"Electricity / Breaker / Lights","label":"Never turns lights on and may immediately turn them off","up":["Mare"],"down":[],"w":34,"rel":"Med"},{"id":"light-shatter-event","cat":"Electricity / Breaker / Lights","label":"Prefers light-shattering events","up":["Mare"],"down":[],"w":24,"rel":"Low"},{"id":"raiju-wide-interference","cat":"Electricity / Breaker / Lights","label":"Electronic interference range feels larger than normal","up":["Raiju"],"down":[],"w":34,"rel":"Med"},{"id":"yokai-short-hearing","cat":"Electricity / Breaker / Lights","label":"During hunts, only hears voice/electronics very close","up":["Yokai"],"down":[],"w":42,"rel":"High"},{"id":"early-hunt","cat":"Hunt Timing / Threshold","label":"Hunts earlier than normal sanity threshold","up":["Demon","Mare","Onryo","Thaye","Raiju","Yokai","Dayan","Kormos","Gallu","Obambo"],"down":["Shade","Deogen"],"w":30,"rel":"Med"},{"id":"demon-ability-hunt","cat":"Hunt Timing / Threshold","label":"Very early hunt that may ignore sanity","up":["Demon"],"down":[],"w":46,"rel":"Med"},{"id":"shade-shy","cat":"Hunt Timing / Threshold","label":"Will not hunt or interact while players are in the same room","up":["Shade"],"down":["Demon","Oni"],"w":42,"rel":"Med"},{"id":"yokai-talking-hunt","cat":"Hunt Timing / Threshold","label":"Talking in same room appears to enable earlier hunt","up":["Yokai"],"down":[],"w":38,"rel":"Med"},{"id":"kormos-sprint-threshold","cat":"Hunt Timing / Threshold","label":"Player sprinting in same room appears to enable earlier hunt","up":["Kormos"],"down":[],"w":36,"rel":"Med"},{"id":"aswang-zero-grace","cat":"Hunt Timing / Threshold","label":"Hunt sometimes appears to start with no grace period","up":["Aswang"],"down":[],"w":36,"rel":"Med"},{"id":"gallu-state-thresholds","cat":"Hunt Timing / Threshold","label":"Hunt threshold changes with normal/enraged/weakened state","up":["Gallu"],"down":[],"w":32,"rel":"Med"},{"id":"obambo-aggressive-hunts","cat":"Hunt Timing / Threshold","label":"Aggressive state hunts earlier but may be shorter","up":["Obambo"],"down":[],"w":34,"rel":"Med"},{"id":"deogen-late-hunt","cat":"Hunt Timing / Threshold","label":"Does not hunt until lower sanity than normal","up":["Deogen"],"down":[],"w":26,"rel":"Low"},{"id":"onryo-flame-prevent","cat":"Fire / Incense / Crucifix","label":"Lit flame nearby prevents hunts like a crucifix","up":["Onryo"],"down":[],"w":48,"rel":"High"},{"id":"onryo-third-blowout","cat":"Fire / Incense / Crucifix","label":"Hunt attempt after third flame blowout with no nearby flame","up":["Onryo"],"down":[],"w":52,"rel":"High"},{"id":"spirit-long-incense","cat":"Fire / Incense / Crucifix","label":"Incense prevents hunts much longer than normal","up":["Spirit"],"down":["Demon"],"w":48,"rel":"High"},{"id":"demon-short-incense","cat":"Fire / Incense / Crucifix","label":"Incense protection seems shorter than normal","up":["Demon"],"down":["Spirit"],"w":46,"rel":"High"},{"id":"demon-crucifix-range","cat":"Fire / Incense / Crucifix","label":"Crucifix blocks hunt from farther away than expected","up":["Demon"],"down":[],"w":32,"rel":"Med"},{"id":"gallu-crucifix-enraged","cat":"Fire / Incense / Crucifix","label":"Crucifix burn causes enraged Gallu behavior","up":["Gallu"],"down":[],"w":38,"rel":"Med"},{"id":"yurei-incense-trap","cat":"Fire / Incense / Crucifix","label":"Non-hunt incense traps it in favorite room","up":["Yurei"],"down":[],"w":32,"rel":"Med"},{"id":"phantom-photo-disappear","cat":"Ghost Events / Manifestation","label":"Ghost disappears when photographed or filmed","up":["Phantom"],"down":[],"w":58,"rel":"High"},{"id":"photo-visible","cat":"Ghost Events / Manifestation","label":"Ghost remains visible in ghost photo","up":[],"down":["Phantom"],"w":32,"rel":"Med"},{"id":"oni-no-mist","cat":"Ghost Events / Manifestation","label":"No mist-form/airball events observed after many events","up":["Oni"],"down":[],"w":34,"rel":"Med"},{"id":"oni-full-visible","cat":"Ghost Events / Manifestation","label":"Very visible during hunts or strong full-form events","up":["Oni"],"down":["Phantom"],"w":35,"rel":"Med"},{"id":"kormos-no-mist-chase","cat":"Ghost Events / Manifestation","label":"Cannot perform mist-form or chasing ghost events","up":["Kormos"],"down":[],"w":32,"rel":"Med"},{"id":"banshee-singing","cat":"Ghost Events / Manifestation","label":"Frequent singing events or unusual singing sanity drain target","up":["Banshee"],"down":[],"w":34,"rel":"Med"},{"id":"phantom-sanity-look","cat":"Ghost Events / Manifestation","label":"Looking at manifestation drains sanity unusually fast","up":["Phantom"],"down":[],"w":30,"rel":"Low"},{"id":"myling-quiet-footsteps","cat":"Sound / Spirit Box","label":"Hunt footsteps/vocalizations only audible when close","up":["Myling"],"down":[],"w":46,"rel":"High"},{"id":"banshee-scream","cat":"Sound / Spirit Box","label":"Banshee scream on parabolic microphone","up":["Banshee"],"down":[],"w":48,"rel":"High"},{"id":"deogen-spiritbox-breath","cat":"Sound / Spirit Box","label":"Deogen breathing response on Spirit Box","up":["Deogen"],"down":[],"w":44,"rel":"High"},{"id":"moroi-curse","cat":"Sound / Spirit Box","label":"Cursed player drains sanity rapidly after paranormal audio/contact","up":["Moroi"],"down":[],"w":42,"rel":"Med"},{"id":"box-alone-mismatch","cat":"Sound / Spirit Box","label":"Spirit Box only works under correct alone/everyone condition","up":[],"down":[],"w":0,"rel":"Context"},{"id":"goryo-camera-dots","cat":"Room / Roaming / D.O.T.S","label":"D.O.T.S visible on camera only, not naked eye","up":["Goryo"],"down":[],"w":50,"rel":"High"},{"id":"goryo-room-stable","cat":"Room / Roaming / D.O.T.S","label":"Favorite room does not naturally change","up":["Goryo"],"down":[],"w":28,"rel":"Low"},{"id":"thaye-high-activity-early","cat":"Room / Roaming / D.O.T.S","label":"Very high activity early, lower activity later","up":["Thaye"],"down":[],"w":36,"rel":"Med"},{"id":"mare-long-roam-lights-on","cat":"Room / Roaming / D.O.T.S","label":"Seems to roam farther when lights are on","up":["Mare"],"down":[],"w":20,"rel":"Low"},{"id":"yurei-door-room","cat":"Room / Roaming / D.O.T.S","label":"Strong door ability or favorite-room trapping behavior","up":["Yurei"],"down":[],"w":38,"rel":"Med"},{"id":"banshee-target","cat":"Targeting / Awareness","label":"Only one player seems targeted during hunts","up":["Banshee"],"down":[],"w":42,"rel":"Med"},{"id":"deogen-knows-location","cat":"Targeting / Awareness","label":"Always knows where players are during hunts","up":["Deogen"],"down":[],"w":44,"rel":"High"},{"id":"kormos-no-los","cat":"Targeting / Awareness","label":"No visual line-of-sight; detects voice/electronics/footsteps instead","up":["Kormos"],"down":[],"w":50,"rel":"High"},{"id":"aswang-hidden-spares","cat":"Targeting / Awareness","label":"Reaches correctly hidden player and hunt ends instead of killing","up":["Aswang"],"down":[],"w":58,"rel":"High"},{"id":"wraith-teleport","cat":"Targeting / Awareness","label":"Teleports to player and leaves EMF at feet level","up":["Wraith"],"down":[],"w":32,"rel":"Med"},{"id":"phantom-travel","cat":"Targeting / Awareness","label":"Travels to random player and leaves EMF at head level","up":["Phantom"],"down":[],"w":28,"rel":"Low"},{"id":"polter-multi-throw","cat":"Object / Interaction","label":"Object pile explosion or many throws at once","up":["Poltergeist"],"down":[],"w":55,"rel":"High"},{"id":"polter-hunt-throw-rate","cat":"Object / Interaction","label":"Throws objects constantly during hunts","up":["Poltergeist"],"down":[],"w":44,"rel":"High"},{"id":"twins-double-interaction","cat":"Object / Interaction","label":"Near-simultaneous interactions in separate places","up":["The Twins"],"down":[],"w":42,"rel":"Med"},{"id":"shade-low-interaction","cat":"Object / Interaction","label":"Low interaction/events while players are near the ghost","up":["Shade"],"down":["Oni","Poltergeist"],"w":34,"rel":"Med"},{"id":"obake-shapeshift","cat":"Object / Interaction","label":"Brief shapeshift/model flicker during hunt","up":["Obake"],"down":[],"w":52,"rel":"High"},{"id":"mimic-fake-orbs","cat":"Mimic / Special Cases","label":"Ghost Orbs plus impossible evidence combo","up":["The Mimic"],"down":[],"w":60,"rel":"High"},{"id":"mimic-changing-tells","cat":"Mimic / Special Cases","label":"Behavior tells change between hunts or over time","up":["The Mimic"],"down":[],"w":44,"rel":"Med"}];
let state={evidence:{},behaviors:{},votes:{},responds:'unknown',evidenceMode:'3'}; let expanded={}; let evidenceCollapsed=localStorage.getItem('phasmoEvidenceCollapsed')==='true'; let behaviorCollapsed=localStorage.getItem('phasmoBehaviorCollapsed')==='true'; let cursedCollapsed=localStorage.getItem('phasmoCursedCollapsed')==='true'; let topPanelCollapsed=localStorage.getItem('phasmoTopPanelCollapsed')==='true'; let sanitySaveTimer=null; let setupDirty=false;
B.push({id:'deildegast-moved-items-slow',cat:'Movement Speed',label:'Starts extremely fast and slows on later hunts after distinct objects are moved',up:['Deildegast'],down:[],w:58,rel:'High'});
function apiUrl(path){return `${API}${path}?room=${encodeURIComponent(room)}${codeSuffix()}`}
async function fetchRoomState(targetRoom=room){
  let r;
  try{r=await fetch(`${API}/state?room=${encodeURIComponent(targetRoom)}${codeSuffixFor(targetRoom)}`);}
  catch(e){renderConnectionStatus(false);return null;}
  if(r.status===403){
    const ok=await retryWithRoomCode('This room is locked. Enter the 4-digit room passcode to join.',targetRoom);
    if(!ok){location.href='/phasmo/rooms';return null;}
    r=await fetch(`${API}/state?room=${encodeURIComponent(targetRoom)}${codeSuffixFor(targetRoom)}`);
  }
  if(r.status===403){
    showAuthError('Room locked. The passcode was not accepted.');
    return null;
  }
  if(r.status===410){
    if(MODE==='room'){
      lastSyncAt=Date.now();
      renderConnectionStatus(true);
      return {...state,roomStatus:'closed',reusingClosedRoom:true};
    }
    location.href='/phasmo/rooms';
    return null;
  }
  if(!r.ok){
    showAuthError('Could not load room state. Please try again.');
    return null;
  }
  const data=await r.json();
  lastSyncAt=Date.now();
  renderConnectionStatus(true);
  return data;
}
async function getState(){let next=await fetchRoomState(room);if(!next)return;state=next;if(!shouldHoldSetupRender())render();}
async function postState(patch){
  let r=await fetch(apiUrl('/state'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});
  if(r.status===403 && await retryWithRoomCode('This room is locked. Enter the 4-digit room passcode to make changes.')){
    r=await fetch(apiUrl('/state'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});
  }
  if(r.status===410){showAuthError('This room session is closed. Create a new room to continue.');return false;}
  if(!r.ok){
    showAuthError('Update blocked. If this room has a passcode, enter the 4-digit code.');
    return false;
  }
  let data=await r.json().catch(()=>null);
  if(data&&data.state){state=data.state;render();}else{await getState();}
  return true;
}
async function command(cmd,user='control'){
  let r=await fetch(apiUrl('/command'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd,user:user,roomPasscode:roomCode})});
  if(r.status===403 && await retryWithRoomCode('This room is locked. Enter the 4-digit room passcode to send commands.')){
    r=await fetch(apiUrl('/command'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd,user:user,roomPasscode:roomCode})});
  }
  if(r.status===410){showAuthError('This room session is closed. Commands are disabled.');return false;}
  if(!r.ok){
    showAuthError('Command blocked. If this room has a passcode, enter the 4-digit code.');
    return false;
  }
  await getState();
  return true;
}
function showAuthError(msg){
  ['authMessage','setupAuthMessage'].forEach(id=>{
    let box=document.getElementById(id);
    if(box){box.textContent=msg;box.classList.remove('hidden');}
  });
}
function renderConnectionStatus(ok=navigator.onLine){
  const el=document.getElementById('connectionStatus'); if(!el)return;
  const online=navigator.onLine!==false;
  el.classList.toggle('offline',!online||!ok);
  if(!online){el.textContent='Offline';return;}
  if(!ok){el.textContent='Reconnecting';return;}
  const age=lastSyncAt?Math.max(0,Math.round((Date.now()-lastSyncAt)/1000)):0;
  el.textContent=age<5?'Synced':`Synced ${age}s`;
}
function isEditableField(el){return !!(el && ['INPUT','SELECT','TEXTAREA'].includes(el.tagName));}
function isSetupLikeMode(){return MODE==='room'||MODE==='setup';}
function isSetupPanelEditing(){const active=document.activeElement;return !!(active&&active.closest&&active.closest('#setupPanel')&&isEditableField(active));}
function shouldHoldSetupRender(){return isSetupLikeMode()&&(setupDirty||isSetupPanelEditing());}
function setValueUnlessEditing(id,value){const el=document.getElementById(id);if(!el)return;if(document.activeElement!==el)el.value=value;}
function impact(g){let s=0; for(const b of B){let v=state.behaviors?.[b.id]||'unknown'; if(v==='observed'){if(b.up.includes(g.name))s+=b.w;if(b.down.includes(g.name))s-=b.w} if(v==='contradicted'){if(b.up.includes(g.name))s-=Math.round(b.w*.65);if(b.down.includes(g.name))s+=Math.round(b.w*.45)}} return s}

function safeRoomName(raw){let v=(raw||'default').toLowerCase().trim().replace(/[^a-z0-9_-]+/g,'-').replace(/^-+|-+$/g,'').slice(0,64);return v||'default'}
function apiUrlFor(targetRoom,path){return `${API}${path}?room=${encodeURIComponent(targetRoom)}${codeSuffixFor(targetRoom)}`}
async function postStateForRoom(targetRoom,patch){let r=await fetch(apiUrlFor(targetRoom,'/state'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});if(r.status===403 && await retryWithRoomCode('This room is locked. Enter the 4-digit room passcode to make changes.',targetRoom)){r=await fetch(apiUrlFor(targetRoom,'/state'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});} if(r.status===410){showAuthError('This room session is closed.');return false;}if(r.status===400){let msg=await r.text().catch(()=>null);showAuthError('Room name blocked. Use a stream-safe room name with letters, numbers, spaces, hyphens, or underscores.');return false;}if(!r.ok){showAuthError('Update blocked. If this room has a passcode, enter the 4-digit code.');return false;}return true}
function cleanSanityValues(vals){let out=[null,null,null,null];(vals||[]).slice(0,4).forEach((v,i)=>{if(v===null||v===undefined||v===''){out[i]=null;return;}let n=Number(v);out[i]=Number.isFinite(n)?Math.max(0,Math.min(100,Math.round(n))):null});return out}
function activeSanityValues(){let vals=cleanSanityValues(state.sanityValues||[]), players=Math.max(1,Math.min(4,+(state.playerCount||4)));return vals.slice(0,players).filter(v=>v!==null)}
function sanityAverage(){let vals=activeSanityValues(); if(!vals.length)return null; return Math.round(vals.reduce((a,b)=>a+b,0)/vals.length)}
function huntRule(name){return HUNT_RULES[name]||{threshold:DEFAULT_HUNT_THRESHOLD,note:'Standard hunt threshold.'}}
function canHuntAt(name,avg){if(avg===null||avg===undefined)return true;let r=huntRule(name);return !!r.any || avg <= r.threshold}
function huntSummary(){let avg=state.huntSanity;if(avg===null||avg===undefined||avg==='')return 'No hunt sanity logged.';let kept=G.filter(g=>canHuntAt(g.name,+avg)).length;return `Hunt logged at ${Math.round(+avg)}% average sanity. ${kept}/${G.length} ghosts can naturally/specially hunt at that sanity.`}
function presentationSummary(){let p=state.presentation||'unknown'; if(p==='male')return 'Male presentation/name: Banshee and Dayan ruled out.'; if(p==='female')return 'Female presentation/name: male-only ghosts ruled out if present in candidate pool.'; return 'Unknown'}
function candidates(){let manual=state.manualGhosts||{}, selected=manual.selected||null, excluded=new Set(manual.excluded||[]), yes=E.filter(k=>state.evidence[k]==='yes'), no=E.filter(k=>state.evidence[k]==='no'), mode=+state.evidenceMode, huntAvg=(state.huntSanity===null||state.huntSanity===undefined||state.huntSanity==='')?null:+state.huntSanity, presentation=state.presentation||'unknown'; let pool=G.filter(g=>{if(selected)return g.name===selected; if(excluded.has(g.name))return false; if(presentation==='male'&&GENDER_RULES[g.name]==='female')return false; if(presentation==='female'&&GENDER_RULES[g.name]==='male')return false; if(!canHuntAt(g.name,huntAvg))return false; if(mode===0&&!yes.length)return true; if(!yes.every(e=>g.ev.includes(e)||(g.name==='The Mimic'&&e==='orbs')))return false; if(mode===3&&no.some(e=>g.ev.includes(e)||(g.name==='The Mimic'&&e==='orbs')))return false; return true}); let result=pool.map(g=>{let hr=huntRule(g.name), hbonus=(huntAvg!==null&&canHuntAt(g.name,huntAvg)&&hr.threshold>=huntAvg?10:0), pbonus=(presentation!=='unknown'&&GENDER_RULES[g.name]===presentation?8:0);return {...g,impact:impact(g),huntRule:hr,score:(selected&&g.name===selected?999:0)+impact(g)+hbonus+pbonus+yes.filter(e=>g.ev.includes(e)).length*22+(g.name==='The Mimic'&&yes.includes('orbs')?12:0)}}).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name)); if(state.fakeCandidate&&!selected){result.push({name:state.fakeCandidate.name||'The Intern',ev:state.fakeCandidate.ev||['box','orbs','writing'],impact:0,huntRule:{threshold:100,any:true},score:-999,fake:true,note:state.fakeCandidate.note||'Not real. Clearly a prank candidate.'})} return result}
function renderHuntRisk(candidateList){
  const level=document.getElementById('huntRiskLevel'), summary=document.getElementById('huntRiskSummary'), detail=document.getElementById('huntRiskGhosts');
  if(!level||!summary||!detail)return;
  const avg=sanityAverage(), pool=(candidateList||candidates()).filter(g=>!g.fake);
  level.className='risk-badge';
  if(avg===null||!pool.length){level.classList.add('risk-unknown');level.textContent=avg===null?'Need sanity':'No candidates';summary.textContent=avg===null?'Enter team sanity to estimate hunt risk.':'No real candidates remain to evaluate.';detail.textContent='Special abilities and cursed hunts can bypass normal thresholds.';return;}
  const normal=pool.filter(g=>avg<=huntRule(g.name).threshold), special=pool.filter(g=>huntRule(g.name).any), earliest=Math.max(...pool.map(g=>huntRule(g.name).threshold));
  let risk='low', label='Low';
  if(normal.length){risk='danger';label='Hunt possible';}
  else if(avg<=earliest+10||special.length){risk='caution';label='Caution';}
  level.classList.add('risk-'+risk);level.textContent=label;
  summary.textContent=`Team average ${avg}%. ${normal.length?`${normal.length} remaining candidate${normal.length===1?' is':'s are'} within a normal hunt threshold.`:`Earliest normal threshold among candidates is ${earliest}%.`}`;
  const normalNames=normal.map(g=>g.name).join(', '), specialNames=special.map(g=>g.name).join(', ');
  detail.textContent=[normalNames?`Can normally hunt now: ${normalNames}.`:'No remaining candidate is at its normal threshold.',specialNames?`Special-condition risk: ${specialNames}.`:'', 'Cursed hunts can bypass normal thresholds.'].filter(Boolean).join(' ');
}
function status(){let c=candidates(), yes=E.filter(k=>state.evidence[k]==='yes'), mode=+state.evidenceMode, target=mode>0&&yes.length>=mode, mimic=c.some(g=>g.name==='The Mimic'); if(!c.length)return{kind:'conflict',name:'Retest',text:'No ghost matches. Recheck evidence.'}; if(target&&c.length===1)return{kind:'locked',name:`Final ID: ${c[0].name}`,text:'Evidence target reached. Behavior is sanity-check only.'}; if(target&&mimic)return{kind:'mimic',name:'Mimic Check',text:'Evidence target reached, but Mimic remains possible.'}; if(target)return{kind:'locked',name:`Likely: ${c[0].name}`,text:'Evidence target reached. Resolve contradictions only.'}; if(c.length===1)return{kind:'verify',name:`Verify ${c[0].name}`,text:'One candidate remains. Final disconfirming check.'}; return{kind:'open',name:'Investigating',text:'Continue evidence collection.'}}
function nextEv(){let st=status(); if(['locked','conflict','verify'].includes(st.kind))return null; let c=candidates(), unk=E.filter(e=>state.evidence[e]==='unknown'); if(c.length<=1||!unk.length)return null; return unk.map(ev=>{let y=0,n=0; for(const g of c){let has=g.ev.includes(ev)||(g.name==='The Mimic'&&ev==='orbs'); has?y++:n++} let split=Math.min(y,n), swing=Math.abs(y-n); return{ev,y,n,split,score:split*10-swing-(ev==='box'&&state.responds==='unknown'?2:0)}}).sort((a,b)=>b.score-a.score||b.split-a.split||a.swing-b.swing)[0]}
function nextBehavior(){let c=candidates(); if(c.length<=1)return null; let cset=new Set(c.map(g=>g.name)); let rows=B.filter(b=>{let v=state.behaviors?.[b.id]||'unknown'; if(v!=='unknown')return false; return b.up.some(g=>cset.has(g))||b.down.some(g=>cset.has(g));}); if(!rows.length)return null; return rows.map(b=>{let up=b.up.filter(g=>cset.has(g)).length, down=b.down.filter(g=>cset.has(g)).length, rel=b.rel==='High'?12:b.rel==='Med'?6:0; return {...b,score:b.w+rel+Math.max(up,down)*8}}).sort((a,b)=>b.score-a.score||b.w-a.w)[0]}
function nextUniqueBehavior(){
  let c=candidates(); if(c.length<=1)return null;
  let cset=new Set(c.map(g=>g.name));
  let rows=B.filter(b=>{
    let v=state.behaviors?.[b.id]||'unknown';
    if(v!=='unknown')return false;
    return b.up.some(g=>cset.has(g))||b.down.some(g=>cset.has(g));
  });
  if(!rows.length)return null;
  return rows.map(b=>{
    let up=b.up.filter(g=>cset.has(g)), down=b.down.filter(g=>cset.has(g));
    let touched=[...new Set([...up,...down])];
    let unique=touched.length===1?28:0;
    let split=(up.length>0&&down.length>0)?18:0;
    let rel=b.rel==='High'?14:b.rel==='Med'?7:0;
    return {...b,uniqueGhost:touched[0]||'',score:b.w+rel+unique+split-Math.max(0,touched.length-1)*2};
  }).sort((a,b)=>b.score-a.score||b.w-a.w)[0];
}
function activeTimers(){
  let now=Date.now(), out=[];
  for(const [k,t] of Object.entries(state.timers||{})){
    if(!t?.running)continue;
    const duration=t.durationSeconds||60;
    const endsAt=(t.startedAt||now)+duration*1000;
    const remain=Math.ceil((endsAt-now)/1000);
    const doneFor=Math.max(0,Math.floor((now-endsAt)/1000));
    // Show completed timers briefly as a recent event, then let them fall out
    // of Notes/Chat instead of rotating forever.
    if(remain<=0 && doneFor>15)continue;
    out.push({key:k,remain,duration,doneFor});
  }
  return out.sort((a,b)=>a.remain-b.remain);
}
function fmtTimer(s){if(s<=0)return 'done'; let m=Math.floor(s/60), r=String(s%60).padStart(2,'0'); return `${m}:${r}`}

function voteSummary(kind='votes'){let source=kind==='guesses'?(state.guesses||{}):(state.votes||{});let counts={}; for(const [user,ghost] of Object.entries(source)){counts[ghost]??=[];counts[ghost].push(user)} return Object.entries(counts).map(([ghost,users])=>({ghost,users,count:users.length})).sort((a,b)=>b.count-a.count||a.ghost.localeCompare(b.ghost))}
function escHtml(v){return String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
function candidateReelHtml(list, confirmed=''){
  const box=document.getElementById('ovGhosts');
  const names=confirmed?[confirmed]:(list||[]).map(g=>g.name);
  if(!box)return '';
  if(!names.length){box.className='ov-ghosts static-mode';return '';}
  if(names.length<=3){
    box.className='ov-ghosts static-mode';
    return names.map(name=>`<span class='badge'>${escHtml(name)}</span>`).join('');
  }
  box.className='ov-ghosts reel-mode';
  const chips=names.map(name=>`<span class='badge'>${escHtml(name)}</span>`).join('');
  return `<div class='ghost-reel'><div class='ghost-reel-track'><span class='ghost-reel-label'>Remaining</span>${chips}<span class='ghost-reel-label'>Remaining</span>${chips}</div></div>`;
}
function populateActualGhostSelect(){let sel=document.getElementById('actualGhostSelect'); if(!sel||sel.dataset.ready==='true')return; sel.innerHTML='<option value="">Select actual ghost…</option>'+G.map(g=>`<option value="${g.name}">${g.name}</option>`).join(''); sel.dataset.ready='true'}
function renderContractResult(){
  populateActualGhostSelect();
  const result=state.contractResult||{};
  const ghost=result.confirmedGhost||'';
  const status=document.getElementById('resultStatus');
  const summary=document.getElementById('resultSummary');
  const sel=document.getElementById('actualGhostSelect');
  const btn=document.getElementById('confirmActualGhost');
  const lb=document.getElementById('resultLeaderboardLink');
  if(lb)lb.href=`/phasmo/leaderboard?room=${encodeURIComponent(room)}${codeSuffix()}`;
  if(sel && ghost)sel.value=ghost;
  if(status)status.textContent=ghost?`confirmed: ${ghost}`:'not confirmed';
  if(btn)btn.textContent=ghost?'Update Result & Re-score':'Confirm & Score';
  if(!summary)return;
  if(!ghost){
    const guessCount=Object.keys(state.guesses||{}).length;
    const voteCount=Object.keys(state.votes||{}).length;
    summary.innerHTML=`No confirmed result yet. Current round has <strong>${guessCount}</strong> lucky guess${guessCount===1?'':'es'} and <strong>${voteCount}</strong> decision vote${voteCount===1?'':'s'} waiting to be verified.`;
    return;
  }
  const cg=+(result.correctGuesses||0), wg=+(result.wrongGuesses||0), cv=+(result.correctVotes||0), wv=+(result.wrongVotes||0);
  summary.innerHTML=`Actual ghost: <strong>${ghost}</strong> • Lucky guesses: <strong>${cg}</strong> correct, <strong>${wg}</strong> debunked • Decision votes: <strong>${cv}</strong> correct, <strong>${wv}</strong> debunked.`;
}
function responseLine(){let r=state.responds||'unknown'; if(r==='alone')return 'Spirit Box board: responds to people who are alone.'; if(r==='everyone')return 'Spirit Box board: responds to everyone.'; return 'Spirit Box response condition unknown. Test solo and group before ruling out.';}
function weatherWarnings(){
  const w=(state.weather||'unknown').toLowerCase();
  const notes=[];
  if(w==='sunrise')notes.push('Warmest weather group: rooms start warmer, so early temperature reads may take longer to separate.');
  if(w==='fog')notes.push('Fog can make visual reads and Ghost Orb confirmation harder. Confirm with deliberate camera sweeps.');
  if(w==='blood-moon')notes.push('Blood Moon is special-event weather. Treat visibility and ambient assumptions with caution.');
  if(w==='light-rain'||w==='heavy-rain')notes.push('Rain can mask quiet audio cues and footsteps. Be careful with Myling-style sound reads.');
  if(w==='heavy-rain')notes.push('Heavy Rain is especially noisy; do not overtrust subtle audio.');
  if(w==='snow')notes.push('Snow is the coldest weather group. Trust thermometer thresholds, not visual cold vibes.');
  if(w==='windy')notes.push('Wind can mask subtle throw/door/audio cues.');
  return notes;
}
function titleCase(s){return (s||'unknown').split(/[- ]+/).map(x=>x?x[0].toUpperCase()+x.slice(1):x).join(' ')}
function setupSummary(){
  const bits=[];
  bits.push('Room: '+room);
  if(state.map&&state.map!=='unknown')bits.push(state.map);
  if(state.difficulty&&state.difficulty!=='unknown')bits.push(titleCase(state.difficulty));
  if(state.weather&&state.weather!=='unknown')bits.push(titleCase(state.weather));
  if(state.responds&&state.responds!=='unknown')bits.push('Responds: '+titleCase(state.responds));
  if(state.playerCount)bits.push(`${state.playerCount} player${+state.playerCount===1?'':'s'}`);
  if((state.controlMode||'helper')==='tracker')bits.push('Control: Tracker');
  if((state.overlayMode||'helper')==='tracker')bits.push('Overlay: Tracker');
  if(state.supportOptIn)bits.push('Support drop-ins welcome');
  return bits.length?bits.join(' • '):'room, map, difficulty, weather, response';
}
function renderSetup(){
  const setupPanel=document.getElementById('setupPanel'); if(!setupPanel)return;
  document.body.classList.toggle('room-mode', MODE==='room');
  document.body.classList.toggle('setup-mode', MODE==='setup');
  document.body.classList.toggle('control-mode', MODE==='control');
  setupPanel.classList.toggle('setup-complete', MODE==='control' && state.setupComplete===true);
  const isRoomSetup = MODE==='room';
  const isRoundSetup = MODE==='setup';
  const title=document.getElementById('setupPanelTitle'); if(title)title.textContent=isRoomSetup?'Room / Game Setup':'Round Setup';
  const help=document.getElementById('setupHelpText'); if(help)help.textContent=isRoomSetup?(state.reusingClosedRoom?'This name belonged to a closed session. Saving creates a fresh room; prior leaderboard and usage history stay preserved.':'Create the shared room and save reusable room settings. Streamer.bot setup is separate and usually only done once.'):'Set only the contract details for this round, then open Control.';
  const saveBtn=document.getElementById('saveSetup'); if(saveBtn)saveBtn.textContent=isRoomSetup?'Save Room & Continue':'Start Round';
  setValueUnlessEditing('setupRoom',room);
  setValueUnlessEditing('setupPlayers',String(state.playerCount||4));
  setValueUnlessEditing('setupEvidenceMode',state.evidenceMode||'3');
  const passBox=document.getElementById('setupPasscode');
  if(passBox && document.activeElement!==passBox){passBox.value=roomCode||''; passBox.placeholder=state.roomLocked?'Room locked — enter 4 digits':'4 digits, optional';}
  const supportChannel=document.getElementById('setupSupportChannel');
  if(supportChannel && document.activeElement!==supportChannel){supportChannel.value=state.supportChannel||'';}
  setValueUnlessEditing('setupMap',state.map||'unknown');
  setValueUnlessEditing('setupDifficulty',state.difficulty||'unknown');
  setValueUnlessEditing('setupWeather',state.weather||'unknown');
  setValueUnlessEditing('setupResponds',state.responds||'unknown');
  const done=state.setupComplete===true;
  document.querySelectorAll('#setupProgress [data-step]').forEach(step=>{
    const key=step.dataset.step;
    step.classList.toggle('active',(MODE==='room'&&key==='room')||(MODE==='setup'&&key==='round')||(MODE==='control'&&key==='control'));
    step.classList.toggle('done',(MODE!=='room'&&key==='room')||(MODE==='control'&&key==='round'&&done));
  });
  const appHome=document.getElementById('appHomeBar');
  if(appHome)appHome.href='/phasmo';
  const appHomeSub=document.getElementById('appHomeSub');
  if(appHomeSub)appHomeSub.textContent=`room: ${room} • ${state.roomLocked?'locked • ':''}${done?'active run':'setup needed'}`;
  const appHomeCta=document.getElementById('appHomeCta');
  if(appHomeCta)appHomeCta.textContent='Home';
  document.getElementById('setupStatus').textContent=isRoomSetup?'room settings':(done?'ready':'setup recommended');
  document.getElementById('setupSummaryLine').textContent=setupSummary();
  const commandLine=state.lastCommand?`Last chat command: ${state.lastCommand} → ${state.lastCommandResult||'received'}`:'';
  const setupCmd=document.getElementById('setupCommandStatus');
  if(setupCmd){setupCmd.textContent=commandLine;setupCmd.classList.toggle('hidden', !commandLine);}
  const controlCmd=document.getElementById('controlCommandStatus');
  if(controlCmd){controlCmd.textContent=commandLine;controlCmd.classList.toggle('hidden', !commandLine);}
  const award=document.getElementById('awardBanner');
  if(award){if(state.awardMessage){award.textContent=`Post-contract award: ${state.awardMessage}`; award.classList.remove('hidden');} else award.classList.add('hidden');}
  const fg=document.getElementById('footerGhost');
  if(fg){fg.classList.toggle('hidden', sessionStorage.getItem('phasmoJumpscarePressed')!=='true');}
  const jumpPanel=document.getElementById('jumpscarePanel');
  if(jumpPanel){jumpPanel.classList.toggle('hidden', state.config && (state.config.allowEasterEggs===false || state.config.allowJumpscareButton===false));}
  const jc=document.getElementById('jumpscareCount'); if(jc && !jc.dataset.revealed){jc.classList.add('hidden');}
  const notes=weatherWarnings();
  const controlWarn=document.getElementById('controlWeatherWarning');
  if(controlWarn){if(notes.length){controlWarn.innerHTML='<strong>Weather caution:</strong> '+notes.join(' ');controlWarn.classList.remove('hidden')} else {controlWarn.classList.add('hidden')}}
  const roundHref=`/phasmo/round?room=${encodeURIComponent(room)}${codeSuffix()}`;
  const roomHref=`/phasmo/room?room=${encodeURIComponent(room)}${codeSuffix()}`;
  const setupLink=document.getElementById('setupRouteLink'); if(setupLink)setupLink.href=roundHref;
  const setupTop=document.getElementById('setupRouteLinkTop'); if(setupTop)setupTop.href=roundHref;
  const configInline=document.getElementById('setupConfigLink'); if(configInline)configInline.href=`/phasmo/config?room=${encodeURIComponent(room)}${codeSuffix()}`;
  const controlInline=document.getElementById('setupControlLink'); if(controlInline)controlInline.href=`/phasmo/control?room=${encodeURIComponent(room)}${codeSuffix()}`;
  const leaderboardLink=document.getElementById('leaderboardRouteLink'); if(leaderboardLink)leaderboardLink.href=`/phasmo/leaderboard?room=${encodeURIComponent(room)}${codeSuffix()}`;
  const configLink=document.getElementById('configLink'); if(configLink)configLink.href=`/phasmo/config?room=${encodeURIComponent(room)}${codeSuffix()}`;
  const releaseLink=document.getElementById('releaseNotesLink'); if(releaseLink)releaseLink.href=`/phasmo/release-notes?room=${encodeURIComponent(room)}`;
  const ackLink=document.getElementById('acknowledgementsLink'); if(ackLink)ackLink.href=`/phasmo/acknowledgements?room=${encodeURIComponent(room)}`;
  const streamerBotLink=document.getElementById('streamerBotLink'); if(streamerBotLink)streamerBotLink.href=`/phasmo/streamerbot?room=${encodeURIComponent(room)}`;
  const bugLink=document.getElementById('bugReportLink'); if(bugLink)bugLink.href=`/phasmo/bug-report?room=${encodeURIComponent(room)}`;
  const controlSummary=document.getElementById('controlSetupSummary');
  if(controlSummary){
    const parts=[]; parts.push(`<strong>Room: ${room}</strong>`);
    if(state.map&&state.map!=='unknown')parts.push(`<strong>${state.map}</strong>`);
    if(state.difficulty&&state.difficulty!=='unknown')parts.push(titleCase(state.difficulty));
    if(state.weather&&state.weather!=='unknown')parts.push(titleCase(state.weather));
    if(state.responds&&state.responds!=='unknown')parts.push('Responds: '+titleCase(state.responds));
    if(state.playerCount)parts.push(`${state.playerCount} player${+state.playerCount===1?'':'s'}`);
    if((state.controlMode||'helper')==='tracker')parts.push('Control: Tracker');
    if((state.overlayMode||'helper')==='tracker')parts.push('Overlay: Tracker');
    controlSummary.innerHTML=parts.length?parts.join(' • '):'Setup not completed.';
  }
}

function render(){ if(MODE==='overlay')renderOverlay(); else renderControl(); }
function renderCursedHelper(){
  const box=document.getElementById('cursedRows'); if(!box)return;
  const map=state.map||'unknown';
  const hint=CURSED_HINTS[map]||'Select a map in setup for location hints. Default contracts usually have one cursed item, so clear known spawns as you check them.';
  document.getElementById('cursedMapHint').textContent=hint;
  const statuses=state.cursedItems||{};
  const found=CURSED_ITEMS.find(item=>(statuses[item.toLowerCase()]||'unknown')==='found');
  if(found){
    const key=found.toLowerCase();
    const loc=(CURSED_LOCATIONS[map]&&CURSED_LOCATIONS[map][found])||'Known spawn for selected map not loaded.';
    const use=CURSED_USE[found]||'Use carefully. Cursed possessions can trigger dangerous/cursed hunt situations.';
    box.innerHTML=`<div class='cursed-row found-card'><div><div class='cursed-name'>${found}</div><div class='cursed-hint'><strong>Location:</strong> ${loc}<br><strong>Use:</strong> ${use}</div></div><button data-cursed='${key}' data-cursed-val='unknown'>Undo</button></div>`;
    document.querySelectorAll('[data-cursed]').forEach(btn=>btn.onclick=()=>postState({cursedItems:{[btn.dataset.cursed]:btn.dataset.cursedVal}}));
    return;
  }
  box.innerHTML=CURSED_ITEMS.map(item=>{
    const key=item.toLowerCase();
    const val=statuses[key]||'unknown';
    const loc=(CURSED_LOCATIONS[map]&&CURSED_LOCATIONS[map][item])||hint;
    if(val==='out'){
      return `<div class='cursed-row out compact'><div><div class='cursed-name'>${item}</div><div class='cursed-hint'>Cleared / not present.</div></div><button data-cursed='${key}' data-cursed-val='unknown'>Undo</button></div>`;
    }
    return `<div class='cursed-row'><div><div class='cursed-name'>${item}</div><div class='cursed-hint'>${loc}</div></div><button class='green' data-cursed='${key}' data-cursed-val='found'>Found</button><button class='grey' data-cursed='${key}' data-cursed-val='out'>Not Present</button><button data-cursed='${key}' data-cursed-val='unknown'>?</button></div>`;
  }).join('');
  document.querySelectorAll('[data-cursed]').forEach(btn=>btn.onclick=()=>postState({cursedItems:{[btn.dataset.cursed]:btn.dataset.cursedVal}}));
}
function renderControl(){document.getElementById('control')?.classList.remove('hidden');renderSetup();
 const controlTrackerMode=(state.controlMode||'helper')==='tracker';
 document.querySelector('.next')?.classList.toggle('hidden', controlTrackerMode);
 document.getElementById('topPanel')?.classList.toggle('collapsed', topPanelCollapsed); const topToggle=document.getElementById('toggleTopPanel'); if(topToggle){topToggle.textContent=topPanelCollapsed?'Expand':'Collapse';topToggle.setAttribute('aria-expanded',String(!topPanelCollapsed));}const roomLabel=document.getElementById('roomLabel'),modeSelect=document.getElementById('mode'),countBadge=document.getElementById('countBadge'),summary=document.getElementById('summary'),respondsHint=document.getElementById('respondsHint');if(roomLabel)roomLabel.textContent=room;if(modeSelect)modeSelect.value=state.evidenceMode;let c=candidates();if(countBadge)countBadge.textContent=c.length+' candidates';if(summary)summary.textContent=`${E.filter(k=>state.evidence[k]==='yes').length} confirmed`;if(respondsHint)respondsHint.textContent=responseLine();renderHuntRisk(c);
 document.getElementById('evidencePanel')?.classList.toggle('collapsed', evidenceCollapsed);
 const evToggle=document.getElementById('toggleEvidence'); if(evToggle){evToggle.textContent=evidenceCollapsed?'Expand':'Collapse';evToggle.setAttribute('aria-expanded',String(!evidenceCollapsed));}
 document.getElementById('behaviorPanel')?.classList.toggle('collapsed', behaviorCollapsed);
 const behaviorToggle=document.getElementById('toggleBehavior'); if(behaviorToggle){behaviorToggle.textContent=behaviorCollapsed?'Expand':'Collapse';behaviorToggle.setAttribute('aria-expanded',String(!behaviorCollapsed));}
 document.getElementById('cursedPanel')?.classList.toggle('collapsed', cursedCollapsed);
 const cursedToggle=document.getElementById('toggleCursed'); if(cursedToggle){cursedToggle.textContent=cursedCollapsed?'Expand':'Collapse';cursedToggle.setAttribute('aria-expanded',String(!cursedCollapsed));}
 let nx=nextEv(), nb=nextBehavior(), st=status(); document.getElementById('nextName').textContent=nx?EL[nx.ev]:(nb?'Behavior: '+nb.cat:st.name); document.getElementById('nextWhy').textContent=nx?`${EL[nx.ev]} splits ${nx.y}/${nx.n}.`+(nx.ev==='box'?` ${responseLine()}`:''):(nb?`${nb.label}. Supports: ${nb.up.join(', ')||'context'}${nb.down.length?`; argues against: ${nb.down.join(', ')}`:''}.`:st.text); document.getElementById('confirmNext').disabled=!(nx||nb);document.getElementById('denyNext').disabled=!(nx||nb);document.getElementById('confirmNext').textContent=nx?'Confirm '+EL[nx.ev]:(nb?'Observed':'Confirmed');document.getElementById('denyNext').textContent=nx?'No '+EL[nx.ev]:(nb?'No / False':'No more evidence'); if(nx){document.getElementById('confirmNext').onclick=()=>postState({evidence:{[nx.ev]:'yes'}});document.getElementById('denyNext').onclick=()=>postState({evidence:{[nx.ev]:'no'}})} else if(nb){document.getElementById('confirmNext').onclick=()=>postState({behaviors:{[nb.id]:'observed'}});document.getElementById('denyNext').onclick=()=>postState({behaviors:{[nb.id]:'contradicted'}})}
 renderTimers(); renderTrackers(); renderManualGhosts(); renderContractResult(); renderCursedHelper();
 document.getElementById('evidenceRows').innerHTML=E.map(k=>{let v=state.evidence[k]||'unknown'; let cls=(want)=>`state ${want} ${(want==='unk'?v==='unknown':v===want)?'active':'inactive'}`; return `<div class='evrow'><span class='evname'>${EL[k]}</span><button class='${cls('yes')}' data-ev='${k}' data-val='yes'>✓</button><button class='${cls('unk')}' data-ev='${k}' data-val='unknown'>?</button><button class='${cls('no')}' data-ev='${k}' data-val='no'>×</button></div>`}).join(''); document.querySelectorAll('[data-ev]').forEach(btn=>btn.onclick=()=>postState({evidence:{[btn.dataset.ev]:btn.dataset.val}}));
 document.getElementById('ghosts').innerHTML=c.slice(0,8).map((g,i)=>`<div class='ghost ${i===0&&g.score>0?'top':''} ${g.fake?'fake-ghost':''}'><h4>${g.name}</h4><div class='tags'>${g.ev.map(e=>`<span class='chip'>${EL[e]||e}</span>`).join('')}${g.ev.includes('box')?`<span class='chip blue'>${state.responds==='alone'?'Box: Alone':state.responds==='everyone'?'Box: Everyone':'Box: Unknown response'}</span>`:''}</div><div class='muted'>${g.fake?(g.note||'Not real. Clearly a prank candidate.'):`${g.impact?`${g.impact>0?'+':''}${g.impact} behavior`:'No behavior'}${state.huntSanity!==null&&state.huntSanity!==undefined&&state.huntSanity!==''?` • Hunt ≤${g.huntRule.threshold}%${g.huntRule.any?' / special':''}`:''}${GENDER_RULES[g.name]?` • ${titleCase(GENDER_RULES[g.name])}-only`:''}`}</div></div>`).join(''); renderVotes(); renderBehaviors();}

function renderTimers(){let box=document.getElementById('timerGrid'); if(!box)return; let timers=['incense','hunt','cooldown']; let map=Object.fromEntries(activeTimers().map(t=>[t.key,t])); box.innerHTML=timers.map(k=>{let t=map[k], val=t?fmtTimer(t.remain):'—'; return `<div class='timer-tile'><div class='timer-name'>${k}</div><div class='timer-val ${t&&t.remain<=0?'done':''}'>${val}</div></div>`}).join('')}
function renderTrackers(){
  const vals=cleanSanityValues(state.sanityValues||[]), players=Math.max(1,Math.min(4,+(state.playerCount||4)));
  const grid=document.querySelector('.sanity-grid'); if(grid)grid.style.setProperty('--players', players);
  for(let i=0;i<4;i++){
    let el=document.getElementById('sanity'+(i+1));
    if(el){
      el.style.display=i>=players?'none':'';
      el.disabled=i>=players;
      el.placeholder=i<players?'P'+(i+1):'—';
      if(document.activeElement!==el) el.value=vals[i]===null?'':vals[i];
    }
  }
  const avg=sanityAverage(); const avgBox=document.getElementById('sanityAverage'); if(avgBox)avgBox.textContent=avg===null?'Avg: —':`Avg: ${avg}%`;
  const hunt=document.getElementById('huntReadout'); if(hunt){hunt.textContent=huntSummary(); hunt.classList.toggle('warning', state.huntSanity!==null&&state.huntSanity!==undefined&&state.huntSanity!=='')}
  const vg=document.getElementById('vanGoblinBadge');
  if(vg){const hasSanity=state.sanityTouched===true&&sanityAverage()!==null; const evidenceMoved=E.some(k=>state.evidence[k]&&state.evidence[k]!=='unknown'); vg.classList.toggle('hidden', !(hasSanity&&!evidenceMoved&&state.setupComplete===true));}
  const mr=document.getElementById('manifestReadout'); if(mr)mr.textContent=presentationSummary();
  document.querySelectorAll('[data-present]').forEach(btn=>{btn.classList.toggle('green',(state.presentation||'unknown')===btn.dataset.present && btn.dataset.present!=='unknown');btn.classList.toggle('grey',(state.presentation||'unknown')===btn.dataset.present && btn.dataset.present==='unknown')});
}
function renderManualGhosts(){let box=document.getElementById('manualGhostSummary'); if(!box)return; let manual=state.manualGhosts||{}, bits=[]; if(manual.selected)bits.push(`<span class='chip green'>Selected: ${manual.selected}</span>`); for(const g of (manual.excluded||[]))bits.push(`<span class='manual-chip'>Out: ${g}</span>`); box.innerHTML=bits.length?`<div class='manual-list'>${bits.join('')}</div>`:'No manual overrides.'}

function renderVotes(){
  let box=document.getElementById('votes');
  let ignoredLine=document.getElementById('ignoredUsersLine');
  if(ignoredLine){let ignored=state.ignoredUsers||[]; ignoredLine.textContent=ignored.length?`Ignored in this room: ${ignored.join(', ')}`:''; ignoredLine.classList.toggle('hidden', !ignored.length)}
  let votes=voteSummary('votes'), guesses=voteSummary('guesses');
  const totalVotes=votes.reduce((a,v)=>a+v.count,0), totalGuesses=guesses.reduce((a,v)=>a+v.count,0);
  const counts=document.getElementById('chatCounts'); if(counts)counts.textContent=`Guesses: ${totalGuesses} • Votes: ${totalVotes}`;
  const compact=document.getElementById('chatCompact');
  if(compact){
    const topVote=votes[0], topGuess=guesses[0];
    let bits=[];
    if(topVote)bits.push(`Leading vote: <strong>${topVote.ghost}</strong> (${topVote.count})`);
    if(topGuess)bits.push(`Top guess: <strong>${topGuess.ghost}</strong> (${topGuess.count})`);
    compact.innerHTML=bits.length?bits.join(' • '):'No chat input yet.';
  }
  if(!box)return;
  let html='';
  if(votes.length){html+=`<div class='vote-section'><div class='muted' style='margin:6px 0'>Decision Votes</div>${votes.map(v=>`<div class='vote-row'><div><div class='vote-name'>${v.ghost}</div><div class='vote-users'>${v.users.join(', ')}</div></div><span class='badge'>${v.count}</span></div>`).join('')}</div>`} else html+=`<p class='muted'>No decision votes.</p>`;
  if(guesses.length){html+=`<div class='vote-section'><div class='muted' style='margin:10px 0 6px'>Lucky Guesses</div>${guesses.map(v=>`<div class='vote-row'><div><div class='vote-name'>${v.ghost}</div><div class='vote-users'>${v.users.join(', ')}</div></div><span class='badge'>${v.count}</span></div>`).join('')}</div>`} else html+=`<p class='muted'>No lucky guesses.</p>`;
  box.innerHTML=html;
}
function renderBehaviors(){let box=document.getElementById('behaviors'), q=(document.getElementById('behaviorFilter').value||'').toLowerCase(), cset=new Set(candidates().map(g=>g.name)), st=status(); box.innerHTML=''; let groups={}; for(const b of B){let logged=(state.behaviors?.[b.id]||'unknown')!=='unknown'; if(q && !(b.label+' '+b.cat+' '+b.up.join(' ')+b.down.join(' ')).toLowerCase().includes(q))continue; let relevant=b.up.some(g=>cset.has(g))||b.down.some(g=>cset.has(g)); if(!relevant&&!logged)continue; if(st.kind==='mimic'&&!logged&&!b.up.includes('The Mimic')&&!b.down.includes('The Mimic'))continue; if(['locked','verify'].includes(st.kind)&&!logged)continue; (groups[b.cat]??=[]).push(b)} for(const cat of Object.keys(groups)){let rows=groups[cat], selected=rows.find(b=>(state.behaviors?.[b.id]||'unknown')!=='unknown'), open=expanded[cat]===true; let el=document.createElement('div');el.className='branch'; let title=document.createElement('button');title.className='branch-title';title.innerHTML=`<span>${open?'▼':'▶'} ${cat}</span><span class='badge'>${selected?'logged':rows.length+' options'}</span>`;title.onclick=()=>{expanded[cat]=!open;renderBehaviors()};el.appendChild(title); if(selected){let v=state.behaviors[selected.id], div=document.createElement('div');div.className='selected '+(v==='contradicted'?'bad':'');let sn=B.findIndex(x=>x.id===selected.id)+1;div.innerHTML=`<strong>#${sn} ${v==='observed'?'✓':'×'} ${selected.label}</strong><div class='tags'>${selected.up.map(g=>`<span class='chip'>↑ ${g}</span>`).join('')}${selected.down.map(g=>`<span class='chip'>↓ ${g}</span>`).join('')}<span class='chip'>${selected.rel}</span></div><div class='row'><button data-clear='${selected.id}'>Clear</button><button class='blue' data-change='${cat}'>Change</button></div>`;el.appendChild(div)} if(open){let body=document.createElement('div');body.className='branch-body'; for(const b of rows){let opt=document.createElement('div');opt.className='option';let bn=B.findIndex(x=>x.id===b.id)+1;opt.innerHTML=`<div class='option-label'>#${bn} ${b.label}</div><div class='tags'>${b.up.map(g=>`<span class='chip'>↑ ${g}</span>`).join('')}${b.down.map(g=>`<span class='chip'>↓ ${g}</span>`).join('')}<span class='chip'>${b.rel}</span></div><div class='grid2'><button class='green' data-beh='${b.id}' data-cat='${cat}' data-val='observed'>Observed</button><button class='red' data-beh='${b.id}' data-cat='${cat}' data-val='contradicted'>No / False</button></div>`;body.appendChild(opt)} el.appendChild(body)} box.appendChild(el)} document.querySelectorAll('[data-clear]').forEach(btn=>btn.onclick=()=>postState({behaviors:{[btn.dataset.clear]:'unknown'}}));document.querySelectorAll('[data-change]').forEach(btn=>{btn.onclick=()=>{expanded[btn.dataset.change]=true;renderBehaviors()}});document.querySelectorAll('[data-beh]').forEach(btn=>btn.onclick=()=>{let rows=B.filter(x=>x.cat===btn.dataset.cat), patch={behaviors:{}}; for(const sib of rows)patch.behaviors[sib.id]='unknown'; patch.behaviors[btn.dataset.beh]=btn.dataset.val; expanded[btn.dataset.cat]=false; postState(patch)})}
function setupOverlay(){
  const CARD_MS=10000;
  const tick=Math.floor(Date.now()/CARD_MS);
  const phase=tick%6;
  const guesses=voteSummary('guesses').slice(0,3);
  const votes=voteSummary('votes').slice(0,3);

  function pick(list, salt=0){
    return list[Math.abs((tick*37 + salt*17 + 11) % list.length)];
  }

  const classifiedTips=[
    {title:'Classified Field Note',sub:'Recovered from a locked filing cabinet in the van.',body:'Subject repeatedly asked “where are you?” despite all available evidence suggesting “too close.”',note:'Classification: Spooky but actionable.'},
    {title:'Classified Field Note',sub:'Redacted investigation memo.',body:'The ghost has requested fewer meetings, clearer objectives, and one dramatic hallway per sprint.',note:'Classification: Union-adjacent.'},
    {title:'Classified Field Note',sub:'Internal audit finding.',body:'The team labeled three different rooms as “definitely the ghost room.” Corrective action: stop guessing with confidence.',note:'Classification: Process failure.'},
    {title:'Classified Field Note',sub:'Archived van telemetry.',body:'Repeated screaming correlated strongly with open microphones and poor hiding spot selection.',note:'Classification: Predictable.'}
  ];
  const roomTips={
    kaizen:{title:'Kaizen Contract',sub:'Continuous improvement, but haunted.',body:'Make the next test the best test. Then write down what changed before everyone blames vibes.',note:'Room-specific field note.'},
    seattle:{title:'Seattle Contract',sub:'Rain risk: emotional and meteorological.',body:'If the ghost throws coffee, assume it is either evidence or a local custom.',note:'Room-specific field note.'},
    imestrellas:{title:'Star Room',sub:'Celestial investigation channel detected.',body:'If the ghost starts acting dramatic, check whether it is haunting the room or auditioning.',note:'Room-specific field note.'}
  };

  const fieldTips=[
  {
    "title": "Evidence First",
    "sub": "Evidence narrows the list. Behavior verifies the answer.",
    "body": "A clean call usually comes from one good test, not seven people yelling ghost names at once.",
    "note": "Recommended process: evidence → behavior → final call."
  },
  {
    "title": "Van Wisdom",
    "sub": "The van is not cowardice. It is remote operations.",
    "body": "Someone watching cameras, sanity, and activity is useful. Someone hiding in the van with snacks is logistics-adjacent.",
    "note": "Respect the support function."
  },
  {
    "title": "Movie Rule",
    "sub": "If the hallway lights flicker, do not monologue.",
    "body": "Horror movies are full of people explaining their feelings to empty rooms. Those people rarely make it to the sequel.",
    "note": "Short callouts. Long feelings later."
  },
  {
    "title": "Ghostbusters Clause",
    "sub": "Specialized equipment beats confident yelling.",
    "body": "Before asking who to call, maybe place the tools correctly and stop standing in front of the camera.",
    "note": "The proton-pack energy is appreciated. The blocked tripod is not."
  },
  {
    "title": "Scooby Protocol",
    "sub": "Running in groups is valid if the group knows where the door is.",
    "body": "A chase montage is only charming when everyone survives it and the hallway layout makes physical sense.",
    "note": "Know the loop before committing to the bit."
  },
  {
    "title": "Found Footage Rule",
    "sub": "If the camera angle is bad, the evidence is bad.",
    "body": "A beautiful shot of a cabinet does not become Ghost Orbs just because we believe in cinema.",
    "note": "Frame the evidence, not the furniture."
  },
  {
    "title": "Spirit Box Manners",
    "sub": "Ask clear questions and give the ghost space to answer.",
    "body": "Six investigators yelling at the box is not teamwork. It is a haunted conference call.",
    "note": "Mute the meeting. Run the test."
  },
  {
    "title": "Thermometer Truth",
    "sub": "Do not let the weather gaslight you.",
    "body": "Cold visuals are spooky. Temperature trends are data. Use the tool, not your goosebumps.",
    "note": "Vibes are not calibrated."
  },
  {
    "title": "Salt Economy",
    "sub": "Salt is cheap. False certainty is expensive.",
    "body": "Use salt to challenge Wraith early and move on. The floor can be seasoned; the investigation should not be.",
    "note": "Fast test, clean decision."
  },
  {
    "title": "Door Baseline",
    "sub": "If everyone opens doors, nobody owns the baseline.",
    "body": "A door cannot be suspicious if three teammates have already treated it like a saloon entrance.",
    "note": "Control the starting condition."
  },
  {
    "title": "Cursed Object Etiquette",
    "sub": "Finding the cursed object is information. Using it is a business decision.",
    "body": "Touching the haunted item without telling the team is not leadership. It is surprise project scope expansion.",
    "note": "Announce before activating chaos."
  },
  {
    "title": "Ghost Adventures Rule",
    "sub": "Taunting is a method, not a personality.",
    "body": "If you provoke the ghost, have a reason, a hiding plan, and preferably someone else holding the camera.",
    "note": "Drama with controls beats drama with casualties."
  },
  {
    "title": "The Exorcist Rule",
    "sub": "When furniture gets theatrical, collect evidence from a distance.",
    "body": "If the room starts acting like it has a union grievance, maybe stop admiring the set design up close.",
    "note": "Observe, do not audition."
  },
  {
    "title": "Poltergeist Pile",
    "sub": "Object piles are tests, not interior decorating.",
    "body": "If you make a throw pile, say so. Otherwise it is just clutter with a theory degree.",
    "note": "Intentional setup prevents mystery garbage."
  },
  {
    "title": "Myling Check",
    "sub": "Footstep audio needs context.",
    "body": "Rain, floors, distance, and panic all lie. Compare sound to equipment range before making the call.",
    "note": "Signal beats spooky acoustics."
  },
  {
    "title": "Camera Crew Note",
    "sub": "If you are filming the investigation, film the investigation.",
    "body": "Viewers can forgive fear. They cannot forgive seven minutes of staring at the underside of a shelf.",
    "note": "Aim with purpose."
  },
  {
    "title": "Paranormal HR",
    "sub": "The ghost room is a workplace hazard.",
    "body": "Before entering, know who is testing, who is watching sanity, and who is legally just screaming for morale.",
    "note": "Role clarity saves lives and content."
  },
  {
    "title": "Objective Discipline",
    "sub": "Optional objectives are optional until someone says content.",
    "body": "Do the safe objectives early. Do not wait until the ghost has become a sprinting lawsuit.",
    "note": "Front-load low-risk work."
  },
  {
    "title": "Mimic Clause",
    "sub": "Contradiction is not always confusion.",
    "body": "If Ghost Orbs appear with behavior that keeps changing, keep The Mimic in the meeting agenda.",
    "note": "Weirdness can be a clue."
  },
  {
    "title": "Paranormal Budgeting",
    "sub": "Smudges are safety inventory.",
    "body": "Do not spend every incense charge proving you are brave. Bravery has a cooldown and a receipt.",
    "note": "Use resources intentionally."
  },
  {
    "title": "Hiding Spot Audit",
    "sub": "Before the hunt, know the shelter.",
    "body": "Finding a hiding spot during a hunt is like writing the evacuation plan during the fire drill.",
    "note": "Audit before emergency."
  },
  {
    "title": "Final Call Check",
    "sub": "One ghost remaining deserves a sanity pass.",
    "body": "When the tool gives a final answer, verify one behavior if the run has been weird. Victory laps attract teeth.",
    "note": "Trust, then verify."
  },
  {
    "title": "D.O.T.S Patience",
    "sub": "Some evidence is shy until the setup is decent.",
    "body": "Move the projector, change the viewing angle, and stop judging the ghost through a doorway sliver.",
    "note": "Coverage creates confidence."
  },
  {
    "title": "UV Discipline",
    "sub": "Check fresh interactions quickly.",
    "body": "Fingerprints do not wait for your personal growth journey. Hit doors, windows, switches, and coolers fast.",
    "note": "Timing matters."
  },
  {
    "title": "Journal Hygiene",
    "sub": "Unknown is better than fake certainty.",
    "body": "If the test was sloppy, leave it unknown. A weak no can wreck the whole run.",
    "note": "Bad data is worse than missing data."
  },
  {
    "title": "Radio Voice",
    "sub": "Clear callouts beat emotional weather reports.",
    "body": "“Hunting, front hall, moving fast” is useful. “Oh no no no no” is relatable but low-resolution.",
    "note": "Panic in HD, please."
  },
  {
    "title": "Cryptid Crossover",
    "sub": "Not every shadow is a new mechanic.",
    "body": "Sometimes the monster is a ghost. Sometimes it is a teammate standing directly in front of the flashlight.",
    "note": "Identify the mundane first."
  },
  {
    "title": "Haunted Kaizen",
    "sub": "Make the next test the best test.",
    "body": "Choose the check that removes the most uncertainty with the least risk. Continuous improvement, but with screaming.",
    "note": "Smarter, not louder."
  },
  {
    "title": "Possession Sweep",
    "sub": "Fixed spawns are free value.",
    "body": "Check the known location, mark the item found or cleared, and stop turning the house into a scavenger opera.",
    "note": "Standard work, spooky workplace."
  },
  {
    "title": "Evidence Ownership",
    "sub": "One person updates the log.",
    "body": "If everyone owns the journal, the journal belongs to the ghost now.",
    "note": "Single source of truth."
  }
];

  const legacyTips=[
  {
    "title": "Tripwire Doctrine",
    "sub": "Dale “Tripwire” Mullins, Ghost Hunter, 1968–2025",
    "body": "“If it responds to Alone, send in the least emotionally stable teammate. They create the cleanest data.”",
    "note": "Cause of death: entered alone; emotionally unstable teammate declined the assignment."
  },
  {
    "title": "Engagement Theory",
    "sub": "Marcy Bell, Ghost Hunter, 1974–2023",
    "body": "“When in doubt, touch the cursed object. The insurance company loves engagement.”",
    "note": "Cause of death: high engagement, low risk assessment."
  },
  {
    "title": "Split-Up Protocol",
    "sub": "Coach Harlan Pike, Ghost Hunter, 1959–2007",
    "body": "“Always split up. Horror movies have proven this creates the most efficient paperwork.”",
    "note": "Cause of death: paperwork was indeed efficient."
  },
  {
    "title": "Negotiation Method",
    "sub": "Kevin No-Clip Park, Ghost Hunter, 1988–2024",
    "body": "“If you hear footsteps, stand perfectly still and negotiate. Ghosts respect confident middle management.”",
    "note": "Cause of death: negotiation failed during the first counteroffer."
  },
  {
    "title": "Thermo Confidence",
    "sub": "Gus “One Degree” Feldman, Ghost Hunter, 1947–1999",
    "body": "“If the room feels cold emotionally, mark Freezing. Instruments only slow down intuition.”",
    "note": "Cause of death: vibes-based metrology."
  },
  {
    "title": "Door Science",
    "sub": "Linda Latchley, Ghost Hunter, 1979–2026",
    "body": "“Open every door immediately. That way the ghost has more options and feels respected.”",
    "note": "Cause of death: uncontrolled variables achieved consciousness."
  },
  {
    "title": "Van Strategy",
    "sub": "Terry “Base Camp” Doyle, Ghost Hunter, 1962–2021",
    "body": "“The safest investigator is the one providing moral support from the van forever.”",
    "note": "Cause of death: technically natural causes; reputation died earlier."
  },
  {
    "title": "Orb Certainty",
    "sub": "Mick Lenscap, Ghost Hunter, 1991–2025",
    "body": "“If you do not see orbs in five seconds, accuse the ghost of hiding evidence from the camera.”",
    "note": "Cause of death: tripod placed facing a tasteful section of drywall."
  },
  {
    "title": "Candle Logic",
    "sub": "Evelyn Matchstick, Ghost Hunter, 1938–1986",
    "body": "“Fire is calming. Bring more candles into the murder room until morale improves.”",
    "note": "Cause of death: morale did not improve."
  },
  {
    "title": "EMF Shortcut",
    "sub": "Barry Beepman, Ghost Hunter, 1982–2022",
    "body": "“If the EMF reader makes any noise at all, call EMF 5. The ghost clearly has electrical opinions.”",
    "note": "Cause of death: overconfidence with a two-star reading."
  },
  {
    "title": "Loop Commitment",
    "sub": "Nate “No Exit” Granger, Ghost Hunter, 1971–2014",
    "body": "“Never learn hiding spots. Confidence is the only hiding spot you need.”",
    "note": "Cause of death: confidence was not line-of-sight proof."
  },
  {
    "title": "Photo Greed",
    "sub": "Polly Snapshot, Ghost Hunter, 1995–2025",
    "body": "“A perfect ghost photo is worth one teammate. Maybe two if the lighting is good.”",
    "note": "Cause of death: exposure triangle became a triangle of regret."
  },
  {
    "title": "Spirit Box Etiquette",
    "sub": "Ronnie Radio Alvarez, Ghost Hunter, 1969–2019",
    "body": "“Ask the Spirit Box personal finance questions. Ghosts love diversified portfolios.”",
    "note": "Cause of death: received aggressive investment advice."
  },
  {
    "title": "Sanity Economy",
    "sub": "Carl Candlewick, Ghost Hunter, 1954–2002",
    "body": "“Pills are for quitters. Real hunters experience the content at full sanity loss.”",
    "note": "Cause of death: content was experienced."
  },
  {
    "title": "Basement Policy",
    "sub": "Franklin Downstairs, Ghost Hunter, 1980–2020",
    "body": "“If the breaker is in the basement, send everyone. Basements are safer in groups of panicking adults.”",
    "note": "Cause of death: group panic exceeded basement capacity."
  },
  {
    "title": "Mimic Theory",
    "sub": "Janet Maybe, Ghost Hunter, 1977–2024",
    "body": "“Every ghost is The Mimic if you argue long enough.”",
    "note": "Cause of death: hypothesis remained unfalsifiable."
  },
  {
    "title": "Evidence Minimalism",
    "sub": "Art “Gut Check” Malone, Ghost Hunter, 1942–1991",
    "body": "“Tools are a crutch. I identify ghosts by room aura and whether my knees feel cursed.”",
    "note": "Cause of death: knees were inconclusive."
  },
  {
    "title": "Hunt Callout",
    "sub": "Sally Siren Okafor, Ghost Hunter, 1986–2026",
    "body": "“During hunts, narrate everything loudly. The ghost appreciates accessibility.”",
    "note": "Cause of death: accessible location data."
  },
  {
    "title": "Cursed Roulette",
    "sub": "Vince Token, Ghost Hunter, 1990–2025",
    "body": "“If you find Tarot Cards, draw until the problem becomes obvious.”",
    "note": "Cause of death: the problem became obvious."
  },
  {
    "title": "UV Patience",
    "sub": "Mabel Glowstick, Ghost Hunter, 1965–2016",
    "body": "“Check fingerprints tomorrow. The ghost should respect your schedule.”",
    "note": "Cause of death: missed the print window."
  },
  {
    "title": "Equipment Respect",
    "sub": "Doug Tripod Mercer, Ghost Hunter, 1951–2008",
    "body": "“Place all equipment in one majestic pile. If the ghost wants to talk, it knows where to find us.”",
    "note": "Cause of death: the pile achieved nothing with dignity."
  },
  {
    "title": "Objective Planning",
    "sub": "Harold Bonus, Ghost Hunter, 1973–2022",
    "body": "“Optional objectives are mandatory if chat says so. This is basic governance.”",
    "note": "Cause of death: motion passed, Harold did not."
  },
  {
    "title": "Weather Read",
    "sub": "June Forecast, Ghost Hunter, 1984–2024",
    "body": "“If it is snowing, all ghosts are cold. Mark Freezing and enjoy the efficiency.”",
    "note": "Cause of death: fast conclusion, slow correction."
  },
  {
    "title": "Smudge Timing",
    "sub": "Owen Incense Reed, Ghost Hunter, 1949–1997",
    "body": "“Use incense immediately upon entering. It establishes dominance and wastes everyone’s safety net.”",
    "note": "Cause of death: dominance remained unconfirmed."
  },
  {
    "title": "Final Answer",
    "sub": "Victor Victory Chen, Ghost Hunter, 1992–2025",
    "body": "“Lock the ghost as soon as someone sounds confident. Confidence is evidence with better posture.”",
    "note": "Cause of death: persuasive teammate."
  },
  {
    "title": "Containment Plan",
    "sub": "Egon-adjacent intern, Ghost Hunter, 1970–1998",
    "body": "“If the ghost looks angry, describe it as focused and offer it a storage solution.”",
    "note": "Cause of death: unauthorized backpack prototype."
  },
  {
    "title": "Paranormal Influencer",
    "sub": "Zane “Full Spectrum” Braddock, Ghost Hunter, 1989–2026",
    "body": "“If the room gets quiet, ask the ghost to like and subscribe. Entities respect the algorithm.”",
    "note": "Cause of death: demonetized during a hunt."
  },
  {
    "title": "Old House Rule",
    "sub": "Lorraine-ish Mallory, Ghost Hunter, 1940–2004",
    "body": "“If the doll moves, politely move closer and ask what it wants.”",
    "note": "Cause of death: doll wanted follow-up questions."
  },
  {
    "title": "Haunted Hotel Tip",
    "sub": "Jackie Torrance, Ghost Hunter, 1961–2001",
    "body": "“Long empty hallways are excellent places to split the party and practice dramatic whispers.”",
    "note": "Cause of death: hallway had notes."
  },
  {
    "title": "Television Method",
    "sub": "Grant Nightvision, Ghost Hunter, 1976–2025",
    "body": "“If nothing happens, yell ‘did you hear that?’ and wait for the editor to solve it.”",
    "note": "Cause of death: editor refused the assignment."
  },
  {
    "title": "Containment Budget",
    "sub": "Ray “Invoice” Stantzwell, Ghost Hunter, 1956–2012",
    "body": "“Never worry about property damage. If the ghost is real, accounting becomes a later-season problem.”",
    "note": "Cause of death: invoice approved by nobody."
  },
  {
    "title": "Mirror Logic",
    "sub": "Candace Reflection, Ghost Hunter, 1993–2024",
    "body": "“If a mirror shows you the ghost room, stare longer. The ghost appreciates eye contact.”",
    "note": "Cause of death: eye contact was accepted."
  },
  {
    "title": "Doll Friendship",
    "sub": "Chucky “No Relation” Mills, Ghost Hunter, 1981–2021",
    "body": "“If the doll looks cursed, give it a nickname. Nicknames build trust.”",
    "note": "Cause of death: trust-building workshop failure."
  },
  {
    "title": "Basement Confidence",
    "sub": "Nancy Flashlight, Ghost Hunter, 1966–1995",
    "body": "“When the basement door opens by itself, walk down slowly and say ‘hello’ like payroll sent you.”",
    "note": "Cause of death: payroll denied involvement."
  },
  {
    "title": "Museum Policy",
    "sub": "Edwin Glasscase, Ghost Hunter, 1932–1982",
    "body": "“Never remove a haunted artifact. Just relocate it to a more photogenic shelf.”",
    "note": "Cause of death: artifact disliked the shelf."
  },
  {
    "title": "Possession Etiquette",
    "sub": "Father Gary Paperwork, Ghost Hunter, 1958–2010",
    "body": "“If someone sounds possessed, ask them to submit a ticket so the team can prioritize it.”",
    "note": "Cause of death: ticket remained pending."
  },
  {
    "title": "Science Corner",
    "sub": "Dr. Bunsen Noakes, Ghost Hunter, 1972–2023",
    "body": "“If the ghost violates physics, politely remind it of the posted lab rules.”",
    "note": "Cause of death: physics declined to enforce."
  },
  {
    "title": "Campfire Rule",
    "sub": "Blair Woodson, Ghost Hunter, 1975–1999",
    "body": "“If lost in the woods, film an apology instead of checking the map.”",
    "note": "Cause of death: poor navigation and worse framing."
  },
  {
    "title": "Cryptid Outreach",
    "sub": "Mothman Steve, Ghost Hunter, 1983–2020",
    "body": "“If you see glowing eyes, compliment the creature’s brand identity.”",
    "note": "Cause of death: brand engagement exceeded forecast."
  }
];

  const card=document.getElementById('ovCard');
  card?.classList.remove('final','pregame-brief','pregame-chat','pregame-comms','pregame-tip','pregame-legacy');
  card?.classList.add('pregame');

  const ovStep=document.getElementById('ovStep');
  ovStep.classList.remove('small','xsmall');

  function setCard(kicker,title,sub,cls){
    card?.classList.add(cls);
    document.getElementById('ovKicker').textContent=kicker;
    ovStep.textContent=title.toUpperCase();
    if(ovStep.textContent.length>20) ovStep.classList.add('xsmall');
    else if(ovStep.textContent.length>14) ovStep.classList.add('small');
    document.getElementById('ovSub').textContent=sub;
    document.getElementById('ovNotes').innerHTML='';
  }

  const classifiedActive=(state.classifiedUntil||0)>Date.now();
  if(classifiedActive){
    const tip=pick(classifiedTips, phase);
    setCard('CLASSIFIED',tip.title,tip.sub,'pregame-legacy');
    document.getElementById('ovEvidence').innerHTML=`<div class='pg-warning'>Authorized personnel only</div><div class='pg-quote'>${tip.body}</div><div class='pg-source'>${tip.note}</div>`;
    {const g=document.getElementById('ovGhosts'); if(g){g.className='ov-ghosts static-mode';g.innerHTML='';}}
    return;
  }
  const roomTip=roomTips[(room||'').toLowerCase()];
  if(roomTip && phase===4){
    setCard('ROOM-SPECIFIC NOTE',roomTip.title,roomTip.sub,'pregame-tip');
    document.getElementById('ovEvidence').innerHTML=`<div class='pg-quote'>${roomTip.body}</div><div class='pg-source'>${roomTip.note}</div>`;
    {const g=document.getElementById('ovGhosts'); if(g){g.className='ov-ghosts static-mode';g.innerHTML='';}}
    return;
  }
  if((state.awardMessage||'') && phase===5){
    setCard('POST-CONTRACT AWARD',state.awardMessage,'Unofficial, unhelpful, and probably deserved.','pregame-comms');
    document.getElementById('ovEvidence').innerHTML=`<div class='pg-headerline'><div class='pg-emblem'>🏆</div><div><div class='pg-mini'>Investigation award</div><div class='pg-main'>${state.awardMessage}</div></div></div>`;
    {const g=document.getElementById('ovGhosts'); if(g){g.className='ov-ghosts static-mode';g.innerHTML='';}}
    return;
  }
  if(phase===0){
    setCard('CHAT BOARD','Lucky Guesses','Bragging rights only. Make your call before evidence ruins the fun.','pregame-chat');
    document.getElementById('ovEvidence').innerHTML=guesses.length?`<div class='pg-pillrow'>${guesses.map(v=>`<span class='pg-pill vote'>${v.ghost}: ${v.count}</span>`).join('')}</div>`:"<div class='pg-headerline'><div class='pg-emblem'>🎲</div><div><div class='pg-mini'>Viewer command</div><div class='pg-main'>Type !guess GhostName</div></div></div>";
  } else if(phase===1){
    setCard('CHAT BOARD','Decision Vote','Use when evidence is thin and chat is being asked to help choose.','pregame-chat');
    document.getElementById('ovEvidence').innerHTML=votes.length?`<div class='pg-pillrow'>${votes.map(v=>`<span class='pg-pill vote'>${v.ghost}: ${v.count}</span>`).join('')}</div>`:"<div class='pg-headerline'><div class='pg-emblem'>☑</div><div><div class='pg-mini'>When asked</div><div class='pg-main'>Vote with !vote GhostName</div></div></div>";
  } else if(phase===2){
    setCard('FIELD COMMS','Command Cheats','Chat and mods can help without opening the control panel.','pregame-comms');
    document.getElementById('ovEvidence').innerHTML="<div class='pg-command'><div class='cmd'><code>!ev orb no</code><span>set evidence yes/no</span></div><div class='cmd'><code>!be 12 yes</code><span>set behavior line</span></div><div class='cmd'><code>!guess ghost</code><span>lucky prediction</span></div><div class='cmd'><code>!vote ghost</code><span>when chat is asked</span></div></div>";
  } else if(phase===3 || phase===4){
    const tip=pick(fieldTips, phase);
    setCard('LOADING TIP',tip.title,tip.sub,'pregame-tip');
    document.getElementById('ovEvidence').innerHTML=`<div class='pg-quote'>${tip.body}</div><div class='pg-source'>${tip.note}</div>`;
  } else {
    const tip=pick(legacyTips, phase);
    setCard('ARCHIVED FIELD NOTE',tip.title,tip.sub,'pregame-legacy');
    document.getElementById('ovEvidence').innerHTML=`<div class='pg-warning'>Recovered advice — not recommended</div><div class='pg-quote'>${tip.body}</div><div class='pg-source'>${tip.note}</div>`;
  }

  {const g=document.getElementById('ovGhosts'); if(g){g.className='ov-ghosts static-mode';g.innerHTML='';}}
}

function renderTrackerOverlay(){
  const now=Date.now();
  const card=document.getElementById('ovCard');
  card?.classList.remove('pregame','pregame-brief','pregame-chat','pregame-comms','pregame-tip','pregame-legacy');
  card?.classList.toggle('panic-note', (state.panicUntil||0)>now);
  let c=candidates();
  const result=state.contractResult||{};
  const icon={dots:'◌',emf5:'⚡',freezing:'❄',orbs:'◉',writing:'✎',box:'▣',uv:'☝'};
  const label={dots:'D.O.T.S Projector',emf5:'EMF Level 5',freezing:'Freezing Temperatures',orbs:'Ghost Orb',writing:'Ghost Writing',box:'Spirit Box',uv:'Ultraviolet'};
  const yesCount=E.filter(k=>state.evidence[k]==='yes').length;
  const noCount=E.filter(k=>state.evidence[k]==='no').length;
  const confirmed=result.confirmedGhost||'';
  const isFinal=!!confirmed || c.length===1;
  card?.classList.toggle('final', isFinal);
  document.getElementById('ovKicker').textContent=confirmed?'CONTRACT RESULT':'GAME STATE';
  const ovStep=document.getElementById('ovStep');
  const stepText=confirmed?confirmed:(c.length===1?c[0].name:`${c.length} CANDIDATES`);
  ovStep.textContent=stepText;
  ovStep.classList.remove('small','xsmall');
  if(stepText.length>18) ovStep.classList.add('xsmall');
  else if(stepText.length>13) ovStep.classList.add('small');
  const setupBits=[];
  if(state.map&&state.map!=='unknown')setupBits.push(state.map);
  if(state.difficulty&&state.difficulty!=='unknown')setupBits.push(titleCase(state.difficulty));
  if(state.weather&&state.weather!=='unknown')setupBits.push(titleCase(state.weather));
  setupBits.push(`${yesCount} confirmed / ${noCount} ruled out`);
  document.getElementById('ovSub').textContent=setupBits.join(' • ');
  document.getElementById('ovGhosts').innerHTML=candidateReelHtml(c, confirmed);
  document.getElementById('ovEvidence').innerHTML=E.map(k=>{
    const v=state.evidence[k]||'unknown';
    return `<span class='ev-dot ${v==='yes'?'yes':v==='no'?'no':''}' title='${label[k]}: ${v}'><span class='ev-mark'>${icon[k]}</span></span>`;
  }).join('');
  let votes=voteSummary('votes').slice(0,1);
  let guesses=voteSummary('guesses').slice(0,1);
  let timers=activeTimers().slice(0,2);
  let noteItems=[];
  if(confirmed)noteItems.push(`<span class='ov-note-good'>✓ Result confirmed: ${confirmed}</span>`);
  if(timers.length){noteItems.push(...timers.map(t=>{
    const ti=t.key==='incense'?'🔥':t.key==='hunt'?'👻':'⏱';
    const done=t.remain<=0;
    return `<span class='ov-note-vote'>${ti} ${titleCase(t.key)} ${done?'done':fmtTimer(t.remain)}</span>`;
  }))}
  if(state.huntSanity!==null&&state.huntSanity!==undefined&&state.huntSanity!=='')noteItems.push(`<span class='ov-note-vote'>🧠 Hunt @ ${state.huntSanity}%</span>`);
  if(votes.length){noteItems.push(...votes.map(v=>`<span class='ov-note-vote'>🗳 Vote: ${v.ghost} ${v.count}</span>`))}
  if(guesses.length){noteItems.push(...guesses.map(v=>`<span class='ov-note-vote'>💬 Guess: ${v.ghost} ${v.count}</span>`))}
  const foundCursed=Object.entries(state.cursedItems||{}).find(([k,v])=>v==='found');
  if(foundCursed)noteItems.push(`<span class='ov-note-vote'>🔮 Cursed: ${titleCase(foundCursed[0])}</span>`);
  if(!noteItems.length)noteItems.push('<span class=\'ov-note-vote\'>Tracker mode: evidence and game state only</span>');
  const noteIndex=Math.floor(now/4000)%noteItems.length;
  document.getElementById('ovNotes').innerHTML=noteItems[noteIndex];
}

function renderOverlay(){
  document.getElementById('overlay').classList.remove('hidden');
  const now=Date.now();
  const panicLayer=document.getElementById('ovPanicTakeover');
  const panicTakeoverActive=(state.panicTakeoverUntil||0)>now;
  if(panicLayer)panicLayer.classList.toggle('hidden', !panicTakeoverActive);
  const jumpLayer=document.getElementById('ovJumpscare'), jumpVid=document.getElementById('ovJumpscareVideo');
  const jumpActive=(state.jumpscareUntil||0)>now;
  if(jumpLayer){
    jumpLayer.classList.toggle('hidden', !jumpActive);
    if(jumpActive && jumpVid && jumpVid.dataset.seq!==String(state.jumpscareSeq||state.jumpscareUntil)){
      jumpVid.dataset.seq=String(state.jumpscareSeq||state.jumpscareUntil);
      try{jumpVid.currentTime=0;jumpVid.volume=1;jumpVid.play();}catch(e){}
    }
    if(!jumpActive && jumpVid){try{jumpVid.pause();jumpVid.currentTime=0;}catch(e){}}
  }
  if(state.setupComplete!==true){setupOverlay();return;}
  if((state.overlayMode||'helper')==='tracker'){renderTrackerOverlay();return;}
  document.getElementById('ovCard')?.classList.remove('pregame','pregame-brief','pregame-chat','pregame-comms','pregame-tip','pregame-legacy');
  document.getElementById('ovCard')?.classList.toggle('panic-note', (state.panicUntil||0)>now);
  let c=candidates(), nx=nextEv(), nb=nextBehavior(), st=status();
  const yesCount=E.filter(k=>state.evidence[k]==='yes').length;
  const narrowedAt=+(state.evidenceNarrowedAt||0);
  const rotateBehaviorReady=(+state.evidenceMode===3 && yesCount>=2 && nx && c.length>1 && narrowedAt && (now-narrowedAt)>300000);
  const rb=rotateBehaviorReady?nextUniqueBehavior():null;
  const showRotatedBehavior=!!(rb && Math.floor(now/8000)%2===1);
  const activeBehavior=showRotatedBehavior?rb:(!nx?nb:null);
  const icon={dots:'◌',emf5:'⚡',freezing:'❄',orbs:'◉',writing:'✎',box:'▣',uv:'☝'};
  const short={dots:'DOT',emf5:'EMF',freezing:'TMP',orbs:'ORB',writing:'WRT',box:'BOX',uv:'UV'};
  const shortName={dots:'DOTS',emf5:'EMF 5',freezing:'FREEZING',orbs:'ORB',writing:'WRITING',box:'SPIRIT BOX',uv:'UV'};
  const label={dots:'D.O.T.S Projector',emf5:'EMF Level 5',freezing:'Freezing Temperatures',orbs:'Ghost Orb',writing:'Ghost Writing',box:'Spirit Box',uv:'Ultraviolet'};
  const isFinal=c.length===1 && !nx;
  const isFinalMimic=isFinal && c[0]?.name==='The Mimic';
  document.getElementById('ovCard')?.classList.toggle('final', isFinal);
  document.getElementById('ovKicker').textContent=isFinalMimic?'MIMIC CHECK':(isFinal?'GHOST':'NEXT TEST');

  let stepText=isFinalMimic?'MIMIC CHECK':(isFinal?c[0].name:(activeBehavior?('CHECK '+activeBehavior.cat.split('/')[0].trim().toUpperCase()):(nx?shortName[nx.ev]:st.name.toUpperCase())));
  const ovStep=document.getElementById('ovStep');
  ovStep.textContent=stepText;
  ovStep.classList.remove('small','xsmall');
  if(stepText.length>18) ovStep.classList.add('xsmall');
  else if(stepText.length>13) ovStep.classList.add('small');

  let subText='';
  if(isFinalMimic){
    subText='Confirm fake Ghost Orbs + UV / Freezing / Spirit Box before leaving.';
  } else if(isFinal){
    subText='Only ghost remaining. Verify behavior before leaving.';
  } else if(activeBehavior){
    subText=`Behavior check: ${activeBehavior.label}${activeBehavior.uniqueGhost?` • ${activeBehavior.uniqueGhost}`:''}`;
  } else if(nx){
    subText=`${label[nx.ev]} split: ${nx.y}/${nx.n}`;
    if(nx.ev==='box' && state.responds && state.responds!=='unknown') subText+=` • Responds: ${titleCase(state.responds)}`;
  } else {
    subText=st.text;
  }
  document.getElementById('ovSub').textContent=subText;

  document.getElementById('ovGhosts').innerHTML=candidateReelHtml(c, isFinal?c[0]?.name:'');

  document.getElementById('ovEvidence').innerHTML=E.map(k=>{
    const v=state.evidence[k]||'unknown';
    return `<span class='ev-dot ${v==='yes'?'yes':v==='no'?'no':''}' title='${label[k]}: ${v}'><span class='ev-mark'>${icon[k]}</span></span>`;
  }).join('');

  let obs=B.filter(b=>(state.behaviors?.[b.id]||'unknown')!=='unknown');
  let votes=voteSummary('votes').slice(0,1);
  let guesses=voteSummary('guesses').slice(0,1);
  let timers=activeTimers().slice(0,2);
  let noteItems=[];
  if(isFinalMimic)noteItems.push(`<span class='ov-note-vote'>🌀 Mimic: confirm fake Ghost Orbs</span>`);
  if(rotateBehaviorReady && rb && !showRotatedBehavior)noteItems.push(`<span class='ov-note-vote'>🔁 2 evidence held 5m: rotating behavior checks</span>`);
  const panicNoteActive=(state.panicUntil||0)>now;
  if(panicNoteActive && !panicTakeoverActive){noteItems.push(`<span class='ov-note-bad'>⚠ PANIC DECLARED</span>`)}
  if(timers.length){noteItems.push(...timers.map(t=>{
    const icon=t.key==='incense'?'🔥':t.key==='hunt'?'👻':'⏱';
    const done=t.remain<=0;
    return `<span class='ov-note-vote'>${icon} ${titleCase(t.key)} ${done?'done':fmtTimer(t.remain)}</span>`;
  }))}
  if(state.huntSanity!==null&&state.huntSanity!==undefined&&state.huntSanity!=='')noteItems.push(`<span class='ov-note-vote'>🧠 Hunt @ ${state.huntSanity}%</span>`);
  const ovHasSanity=state.sanityTouched===true&&sanityAverage()!==null, ovEvidenceMoved=E.some(k=>state.evidence[k]&&state.evidence[k]!=='unknown');
  if(ovHasSanity&&!ovEvidenceMoved){noteItems.push(`<span class='ov-note-good'>🧌 Van Goblin activity</span>`)}
  if(obs.length){noteItems.push(...obs.slice(0,2).map(b=>`<span class='${state.behaviors[b.id]==='observed'?'ov-note-good':'ov-note-bad'}'>${state.behaviors[b.id]==='observed'?'✓':'×'} ${b.label}</span>`))}
  if(votes.length){noteItems.push(...votes.map(v=>`<span class='ov-note-vote'>🗳 Vote: ${v.ghost} ${v.count}</span>`))}
  if(guesses.length){noteItems.push(...guesses.map(v=>`<span class='ov-note-vote'>💬 Guess: ${v.ghost} ${v.count}</span>`))}
  if((state.presentation||'unknown')!=='unknown')noteItems.push(`<span class='ov-note-vote'>👤 ${titleCase(state.presentation)} model/name clue</span>`);
  const cautions=weatherWarnings();
  if(cautions.length) noteItems.push(`<span class='ov-note-vote'>🌦 Weather caution</span>`);
  if(!noteItems.length)noteItems.push('<span class=\'ov-note-vote\'>!guess = luck<br>!vote = when asked</span>');
  const noteIndex=Math.floor(now/4000)%noteItems.length;
  document.getElementById('ovNotes').innerHTML=noteItems[noteIndex];
}
document.addEventListener('click',e=>{let r=e.target.dataset.responds;if(r)postState({responds:r}); let tc=e.target.dataset.timerCmd;if(tc)command(tc,'control')});
document.querySelectorAll('#setupPanel input,#setupPanel select,#setupPanel textarea').forEach(el=>{
  el.addEventListener('input',()=>{setupDirty=true;});
  el.addEventListener('change',()=>{setupDirty=true;});
});
document.getElementById('saveSetup')?.addEventListener('click',async()=>{
  const rawRoom=document.getElementById('setupRoom')?.value||room;
  if(!/^[A-Za-z0-9][A-Za-z0-9 _-]{1,31}$/.test(rawRoom.trim())){showAuthError('Use a stream-safe room name: 3–32 characters, letters/numbers/spaces/hyphens/underscores only.');return;}
  const targetRoom=safeRoomName(rawRoom);
  const passcode=rememberRoomCodeFor(targetRoom,document.getElementById('setupPasscode')?.value||storedRoomCodeFor(targetRoom)||'');
  let patch={};
  if(MODE==='room'){
    patch={createRoom:true,roomPasscode:passcode,supportChannel:document.getElementById('setupSupportChannel')?.value||''};
  } else {
    patch={setupComplete:true,playerCount:+document.getElementById('setupPlayers').value||4,evidenceMode:document.getElementById('setupEvidenceMode')?.value||'3',map:document.getElementById('setupMap').value,difficulty:document.getElementById('setupDifficulty').value};
  }
  const ok=await postStateForRoom(targetRoom,patch);
  if(ok) setupDirty=false;
  if(ok && MODE==='room') location.href=`/phasmo/round?room=${encodeURIComponent(targetRoom)}${passcode?'&code='+encodeURIComponent(passcode):''}`;
  if(ok && MODE==='setup') location.href=`/phasmo/control?room=${encodeURIComponent(targetRoom)}${passcode?'&code='+encodeURIComponent(passcode):''}`;
});
function currentSanityInputs(){return [1,2,3,4].map(i=>document.getElementById('sanity'+i)?.value||null)}
function saveSanityNow(){postState({sanityValues:currentSanityInputs()})}
document.getElementById('saveSanity')?.addEventListener('click',saveSanityNow);
[1,2,3,4].forEach(i=>document.getElementById('sanity'+i)?.addEventListener('input',()=>{clearTimeout(sanitySaveTimer); sanitySaveTimer=setTimeout(saveSanityNow,700)}));
document.getElementById('logHunt')?.addEventListener('click',()=>{let vals=[1,2,3,4].map(i=>document.getElementById('sanity'+i)?.value||null), clean=cleanSanityValues(vals), players=+state.playerCount||4, active=clean.slice(0,players).filter(v=>v!==null), avg=active.length?Math.round(active.reduce((a,b)=>a+b,0)/active.length):sanityAverage(); if(avg!==null)postState({sanityValues:clean,huntSanity:avg});});
document.getElementById('clearHunt')?.addEventListener('click',()=>postState({huntSanity:null}));
document.querySelectorAll('[data-present]').forEach(btn=>btn.addEventListener('click',()=>postState({presentation:btn.dataset.present})));
document.getElementById('mode')?.addEventListener('change',e=>postState({evidenceMode:e.target.value}));document.getElementById('setupWeather')?.addEventListener('change',e=>postState({weather:e.target.value}));document.getElementById('setupResponds')?.addEventListener('change',e=>postState({responds:e.target.value}));document.getElementById('reset')?.addEventListener('click',async()=>{if(!confirm('Reset Current Round clears evidence, behaviors, timers, guesses, and votes for this contract only. It does not close the room. Continue?'))return; const ok=await postState({reset:true}); if(ok) location.href=`/phasmo/round?room=${encodeURIComponent(room)}${codeSuffix()}`;});
function showNewRoundModal(){const map=document.getElementById('newRoundMap'),players=document.getElementById('newRoundPlayers'),difficulty=document.getElementById('newRoundDifficulty');if(map)map.value='unknown';if(players)players.value=String(state.playerCount||4);if(difficulty)difficulty.value=state.difficulty||'unknown';document.getElementById('resultModal')?.classList.add('hidden');document.getElementById('newRoundModal')?.classList.remove('hidden');}
async function startNextRound(){showNewRoundModal();}
function showResultModal(){populateActualGhostSelect();renderContractResult();document.getElementById('resultModal')?.classList.remove('hidden');}
document.getElementById('nextRound')?.addEventListener('click',async()=>{
  const hasGuesses=Object.keys(state.guesses||{}).length>0;
  const hasVotes=Object.keys(state.votes||{}).length>0;
  const confirmed=!!(state.contractResult&&state.contractResult.confirmedGhost);
  if((hasGuesses||hasVotes)&&!confirmed){showResultModal();return;}
  await startNextRound();
});
document.getElementById('copyOverlay')?.addEventListener('click',async()=>{await navigator.clipboard?.writeText(`${location.origin}/phasmo/overlay?room=${encodeURIComponent(room)}${codeSuffix()}`);showEasterToast('Overlay URL copied');});
document.getElementById('endSession')?.addEventListener('click',async()=>{if(!confirm('End Session closes this room, removes it from Active Rooms, and stops normal edits/commands. Leaderboard history stays saved. Continue?'))return; const ok=await postState({endSession:true,closedBy:'control'}); if(ok) location.href='/phasmo';});
document.getElementById('confirmActualGhost')?.addEventListener('click',async()=>{const ghost=document.getElementById('actualGhostSelect')?.value||''; if(!ghost){showAuthError('Select the actual ghost before confirming the contract result.');return;} const ok=await postState({contractResult:{confirmedGhost:ghost,confirmedBy:'control'}}); if(ok) await startNextRound();});
document.getElementById('skipScoringNextRound')?.addEventListener('click',startNextRound);
document.getElementById('cancelResultModal')?.addEventListener('click',()=>document.getElementById('resultModal')?.classList.add('hidden'));
document.getElementById('cancelNewRound')?.addEventListener('click',()=>document.getElementById('newRoundModal')?.classList.add('hidden'));
document.getElementById('confirmNewRound')?.addEventListener('click',async()=>{const map=document.getElementById('newRoundMap')?.value||'unknown';if(map==='unknown'){showAuthError('Choose the new map before starting the round.');return;}const button=document.getElementById('confirmNewRound');if(button)button.disabled=true;const ok=await postState({nextRound:true,map,difficulty:document.getElementById('newRoundDifficulty')?.value||state.difficulty||'unknown',playerCount:+document.getElementById('newRoundPlayers')?.value||state.playerCount||4,setupComplete:true});if(button)button.disabled=false;if(ok){document.getElementById('newRoundModal')?.classList.add('hidden');showEasterToast(`New round started: ${map}`);document.querySelector('.app')?.scrollTo({top:0,behavior:'smooth'});}});
document.getElementById('toggleChatDetails')?.addEventListener('click',()=>{const d=document.getElementById('chatDetails'); if(!d)return; d.classList.toggle('hidden'); document.getElementById('toggleChatDetails').textContent=d.classList.contains('hidden')?'View details':'Hide details';});
document.getElementById('behaviorFilter')?.addEventListener('input',renderBehaviors);
document.getElementById('toggleTopPanel')?.addEventListener('click',()=>{topPanelCollapsed=!topPanelCollapsed;localStorage.setItem('phasmoTopPanelCollapsed',topPanelCollapsed);renderControl();});
document.getElementById('toggleEvidence')?.addEventListener('click',()=>{evidenceCollapsed=!evidenceCollapsed;localStorage.setItem('phasmoEvidenceCollapsed',evidenceCollapsed);renderControl();});
document.getElementById('toggleBehavior')?.addEventListener('click',()=>{behaviorCollapsed=!behaviorCollapsed;localStorage.setItem('phasmoBehaviorCollapsed',behaviorCollapsed);renderControl();});
document.getElementById('toggleCursed')?.addEventListener('click',()=>{cursedCollapsed=!cursedCollapsed;localStorage.setItem('phasmoCursedCollapsed',cursedCollapsed);renderControl();});
document.getElementById('copyDiagnostics')?.addEventListener('click',async()=>{
  const details=[
    `Phasmo Helper ${document.getElementById('appVersion')?.textContent||'unknown'}`,
    `Room: ${room}`,
    `Mode: ${MODE}`,
    `Page: ${location.href}`,
    `Browser online: ${navigator.onLine}`,
    `Last sync: ${lastSyncAt?new Date(lastSyncAt).toISOString():'not synced'}`,
    `State version: ${state.stateVersion||0}`,
    `Setup complete: ${state.setupComplete===true}`
  ].join('\n');
  try{await navigator.clipboard.writeText(details);showEasterToast('Diagnostics copied - no passcode or token included');}
  catch(e){showEasterToast('Could not copy diagnostics');}
});
window.addEventListener('online',()=>renderConnectionStatus(true));
window.addEventListener('offline',()=>renderConnectionStatus(false));
function dangerButtonLabel(count){
  if(count>=100)return 'Fine. Touch the haunted button.';
  if(count>=50)return 'You people are the problem.';
  if(count>=10)return 'Seriously, don’t.';
  return 'Don’t press this button';
}
const jb=document.getElementById('jumpscareButton'); if(jb)jb.textContent=dangerButtonLabel(state.jumpscareCount||0);
document.getElementById('jumpscareButton')?.addEventListener('click',async()=>{
  try{
    const r=await fetch(`${API}/jumpscare?room=${encodeURIComponent(room)}`,{method:'POST'});
    const data=await r.json().catch(()=>null);
    if(data&&data.state){state=data.state;}
    const count=(data&&typeof data.count==='number')?data.count:(state.jumpscareCount||0);
    const jc=document.getElementById('jumpscareCount');
    if(jc){
      jc.dataset.revealed='true';
      jc.textContent=`This button has been pressed ${count} time${count===1?'':'s'} by the community.`;
      jc.classList.remove('hidden');
    }
    const btn=document.getElementById('jumpscareButton'); if(btn)btn.textContent=dangerButtonLabel(count);
    sessionStorage.setItem('phasmoJumpscarePressed','true');
    const fg=document.getElementById('footerGhost'); if(fg)fg.classList.remove('hidden');
  }catch(e){}
  const modal=document.getElementById('jumpscareModal'), vid=document.getElementById('jumpscareVideo');
  if(modal){modal.classList.add('show');modal.setAttribute('aria-hidden','false');}
  if(vid){try{vid.currentTime=0; await vid.play();}catch(e){}}
});
document.getElementById('jumpscareClose')?.addEventListener('click',()=>{const modal=document.getElementById('jumpscareModal'), vid=document.getElementById('jumpscareVideo'); if(vid){vid.pause();vid.currentTime=0;} if(modal){modal.classList.remove('show');modal.setAttribute('aria-hidden','true');}});

function clientId(){
  let id=localStorage.getItem('phasmoClientId');
  if(!id){id='browser-'+Math.random().toString(36).slice(2)+'-'+Date.now().toString(36);localStorage.setItem('phasmoClientId',id);}
  return id;
}
function maybeShowFeedbackPrompt(){
  if(MODE!=='setup')return;
  const key='phasmoSetupViews';
  const views=(parseInt(localStorage.getItem(key)||'0',10)||0)+1;
  localStorage.setItem(key,String(views));
  const last=parseInt(localStorage.getItem('phasmoFeedbackLastAt')||'0',10)||0;
  const sevenDays=7*24*60*60*1000;
  if(views>=2 && views%5===0 && Date.now()-last>sevenDays){
    document.getElementById('feedbackPanel')?.classList.remove('hidden');
  }
}
async function sendFeedback(rating){
  const status=document.getElementById('feedbackStatus');
  if(status)status.textContent='Sending feedback…';
  try{
    const payload={rating,room,clientId:clientId(),pageUrl:location.href,user:localStorage.getItem('phasmoUserName')||''};
    const r=await fetch('/api/phasmo/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(!r.ok)throw new Error('feedback failed');
    localStorage.setItem('phasmoFeedbackLastAt',String(Date.now()));
    if(status)status.textContent='Thanks — feedback saved.';
    setTimeout(()=>document.getElementById('feedbackPanel')?.classList.add('hidden'),900);
  }catch(e){
    if(status)status.textContent='Could not send feedback. Try the bug report link if something is broken.';
  }
}
document.querySelectorAll('[data-feedback]').forEach(btn=>btn.addEventListener('click',()=>sendFeedback(btn.dataset.feedback)));
document.getElementById('dismissFeedback')?.addEventListener('click',()=>{localStorage.setItem('phasmoFeedbackLastAt',String(Date.now()));document.getElementById('feedbackPanel')?.classList.add('hidden');});

function showEasterToast(msg){
  let old=document.getElementById('easterToast'); if(old)old.remove();
  let el=document.createElement('div'); el.id='easterToast'; el.className='easter-toast'; el.textContent=msg; document.body.appendChild(el);
  setTimeout(()=>el.remove(),3600);
}
const konami=['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
let konamiPos=0;
document.addEventListener('keydown',async(e)=>{
  const key=(e.key||'').length===1?e.key.toLowerCase():e.key;
  if(key===konami[konamiPos]){
    konamiPos++;
    if(konamiPos>=konami.length){
      konamiPos=0;
      if(state.config && state.config.allowEasterEggs===false){
        showEasterToast('EASTER EGGS DISABLED IN CONFIG');
        return;
      }
      const until=Date.now()+90000;
      state.classifiedUntil=until;
      render();
      showEasterToast('CLASSIFIED FIELD NOTES SENT TO OVERLAY');
      await postState({classifiedUntil:until});
    }
  } else {
    konamiPos=(key===konami[0])?1:0;
  }
});



async function loadAppVersion(){
  const el=document.getElementById('appVersion');
  if(!el)return;
  try{
    const r=await fetch('/api/phasmo/version');
    if(!r.ok)throw new Error('version failed');
    const data=await r.json();
    const version=data.version||'unknown';
    const commit=data.commit?` • ${String(data.commit).slice(0,7)}`:'';
    el.textContent=version+commit;
  }catch(e){
    el.textContent='unknown';
  }
}

async function loadSiteBanner(){
  const el=document.getElementById('siteBanner'), text=document.getElementById('siteBannerText');
  if(!el||!text)return;
  try{
    const r=await fetch('/api/phasmo/banner');
    const data=await r.json();
    const b=data.banner||{};
    if(!b.enabled||!b.message){el.classList.add('hidden');return;}
    const key='phasmoBannerDismissed:'+String(b.updatedAt||'current');
    if(localStorage.getItem(key)==='true'){el.classList.add('hidden');return;}
    text.textContent=b.message;
    el.classList.remove('hidden');
    document.getElementById('dismissSiteBanner')?.addEventListener('click',()=>{localStorage.setItem(key,'true');el.classList.add('hidden');},{once:true});
  }catch(e){}
}

async function pollState(){
  const holdSetupRender=shouldHoldSetupRender();
  let next=await fetchRoomState(room);
  if(!next){renderConnectionStatus(false);return;}
  const unchanged=Number(next.stateVersion||0)===Number(state.stateVersion||0) && Number(next.updatedAt||0)===Number(state.updatedAt||0);
  if(unchanged && MODE!=='overlay'){
    // Timers and connectivity need a cheap tick; the full evidence/candidate DOM does not.
    renderTimers();
    renderConnectionStatus(true);
    return;
  }
  // Do not auto-redirect away from Round Setup. Streamers may intentionally return here during an active run.
  if(holdSetupRender){
    // Keep remote updates in memory, but do not repaint over local room/round setup edits.
    state=next;
    return;
  }
  state=next;
  render();
}
renderConnectionStatus(false); loadAppVersion(); loadSiteBanner(); getState().then(()=>maybeShowFeedbackPrompt()); setInterval(pollState, (MODE==='overlay'?1000:(MODE==='control'?2000:5000))); setInterval(()=>renderConnectionStatus(true),5000);

// Shared workspace chrome is intentionally independent of the investigation renderer.
const experienceToggle=document.getElementById('experienceToggle');
if(experienceToggle){
  const applyExperience=mode=>{document.body.classList.toggle('experience-advanced',mode==='advanced');experienceToggle.textContent=mode==='advanced'?'Basic':'Advanced';localStorage.setItem('phasmoExperience',mode)};
  applyExperience(localStorage.getItem('phasmoExperience')||'basic');
  experienceToggle.addEventListener('click',()=>applyExperience(document.body.classList.contains('experience-advanced')?'basic':'advanced'));
}
for(const [id,path] of [['navTimeline','/phasmo/timeline'],['navIntegrations','/phasmo/integrations']]){const el=document.getElementById(id);if(el)el.href=`${path}?room=${encodeURIComponent(room)}`}
fetch(`/api/phasmo/streamerbot/status?room=${encodeURIComponent(room)}`).then(r=>r.ok?r.json():null).then(data=>{if(!data)return;const status=data.integration||{},el=document.getElementById('workspaceIntegration');if(el)el.textContent=status.connected?`Streamer.bot connected · ${status.latencyMs||0} ms`:'Streamer.bot waiting'}).catch(()=>{});
