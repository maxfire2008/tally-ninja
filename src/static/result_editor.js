"use strict";
/* example usage:
/  const data = {'type': 'race', 'name': 'Duathlon Short Course', 'distance': 'short_course', 'date': datetime.date(2023, 7, 1), 'results': {'donald_trump': {'finish_time': 3473430}, 'joe_biden': {'finish_time': 3382120}, 'kamala_harris': {'finish_time': 2537320}, 'hillary_clinton': {'finish_time': 2964450}, 'mitch_mcconnell': {'DNF': True}, 'nancy_pelosi': {'finish_time': 2172180}, 'bernie_sanders': {'finish_time': 9123850}, 'elizabeth_warren': {'finish_time': 2172180}}, '_filepath': '..\\sample_data\\results\\duathlon\\2023-07-duathlon-short.yaml', '_filename': '2023-07-duathlon-short.yaml'}
/  const athlete_list = {"bernie_sanders":{"_filename":"bernie_sanders.yaml","_filepath":"../sample_data/athletes/bernie_sanders.yaml","dob":"Mon, 08 Sep 1941 00:00:00 GMT","gender":"male","name":"Bernie Sanders","team":"blue"}, "kamala_harris":{"_filename":"kamala_harris.yaml","_filepath":"../sample_data/athletes/kamala_harris.yaml","dob":"Tue, 20 Oct 1964 00:00:00 GMT","gender":"female","name":"Kamala Harris","team":"blue"}}
/  const result_editor = new ResultEditor(data);
*/

let last_id = 0;

function new_id() {
  last_id += 1;
  return last_id;
}

function millisecondsToHhmmss(milliseconds) {
  if (!Number.isInteger(milliseconds)) {
    throw new TypeError("milliseconds must be an integer");
  }

  const secondsTotal = milliseconds / 1000;
  const hours = Math.floor(secondsTotal / 3600);
  const minutes = Math.floor((secondsTotal % 3600) / 60);
  const seconds = Math.floor(secondsTotal % 60);
  const decimalPart = (secondsTotal % 1).toFixed(3).substring(1);

  let output = "";

  if (hours > 0) {
    output += hours + ":";
  }
  if (minutes > 0) {
    output += minutes.toString().padStart(2, "0") + ":";
  }
  output += seconds.toString().padStart(2, "0");
  if (decimalPart > 0) {
    output += decimalPart;
  }

  return output;
}

function hhmmssToMilliseconds(hhmmss) {
  hhmmss = hhmmss.toString();

  if (hhmmss.split(".").length >= 2 && hhmmss.split(".")[1].length > 3) {
    throw new Error("More than 3 digits after the decimal point in " + hhmmss);
  }

  const hhmmssSplit = hhmmss.split(":");
  let seconds = parseFloat(hhmmssSplit[hhmmssSplit.length - 1]);

  if (hhmmssSplit.length > 1) {
    seconds += parseFloat(hhmmssSplit[hhmmssSplit.length - 2]) * 60;
  }
  if (hhmmssSplit.length > 2) {
    seconds += parseFloat(hhmmssSplit[hhmmssSplit.length - 3]) * 3600;
  }

  return Math.round(seconds * 1000);
}

class ResultEditor {
  constructor(data) {
    this.data = data;
    const header = document.getElementById("header");

    const nameDiv = document.createElement("div");
    const nameLabel = document.createElement("label");
    nameLabel.htmlFor = "name";
    nameLabel.textContent = "Name";
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.id = "name";
    nameInput.value = data.name;
    nameInput.onchange = () => {
      this.data.name = nameInput.value;
    };
    nameDiv.appendChild(nameLabel);
    nameDiv.appendChild(nameInput);
    header.appendChild(nameDiv);

    const distanceDiv = document.createElement("div");
    const distanceLabel = document.createElement("label");
    distanceLabel.htmlFor = "distance";
    distanceLabel.textContent = "Distance";
    const distanceInput = document.createElement("input");
    distanceInput.type = "text";
    distanceInput.id = "distance";
    distanceInput.value = data.distance;
    distanceInput.onchange = () => {
      this.data.distance = distanceInput.value;
    };
    distanceDiv.appendChild(distanceLabel);
    distanceDiv.appendChild(distanceInput);
    header.appendChild(distanceDiv);

    const dateDiv = document.createElement("div");
    const dateLabel = document.createElement("label");
    dateLabel.htmlFor = "date";
    dateLabel.textContent = "Date";
    const dateInput = document.createElement("input");
    dateInput.type = "date";
    dateInput.id = "date";
    dateInput.value = data.date;
    dateInput.onchange = () => {
      this.data.date = dateInput.value;
    };
    dateDiv.appendChild(dateLabel);
    dateDiv.appendChild(dateInput);
    header.appendChild(dateDiv);

    this.results = [];
    for (const athlete_id in data.results) {
      this.results.push(new Result(athlete_id, data.results[athlete_id]));
    }
  }

  save() {
    const data = this.data;
    data.results = {};
    for (const result of this.results) {
      data.results[result.athlete_id] = result.data;
    }
    console.log(data);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/save_result");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(data));
  }
}

class Result {
  constructor(athlete_id, data) {
    this.athlete_id = athlete_id;
    this.data = data;
    this.id = new_id();

    this.element = document.createElement("tr");
    this.element.className = "result";

    const athleteCell = document.createElement("td");
    this.athleteButton = document.createElement("button");
    this.athleteButton.id = "athlete" + this.id;
    this.athleteButton.textContent = athlete_list[athlete_id].name;
    this.athleteButton.onclick = () => {
      chooseAthlete((athlete_id) => {
        this.athleteButton.textContent = athlete_list[athlete_id].name;
        this.athlete_id = athlete_id;
        updateWarnings();
      });
    };
    athleteCell.appendChild(this.athleteButton);
    this.element.appendChild(athleteCell);

    const finishTimeCell = document.createElement("td");
    const finishTimeInput = document.createElement("input");
    finishTimeInput.type = "text";
    finishTimeInput.id = "finish_time" + this.id;
    if (data.finish_time === undefined) {
      finishTimeInput.value = "";
    } else {
      finishTimeInput.value = millisecondsToHhmmss(data.finish_time);
    }
    finishTimeInput.onchange = () => {
      this.data.finish_time = hhmmssToMilliseconds(finishTimeInput.value);
    };
    finishTimeCell.appendChild(finishTimeInput);
    this.element.appendChild(finishTimeCell);

    const dnfCell = document.createElement("td");
    const dnfInput = document.createElement("input");
    dnfInput.type = "checkbox";
    dnfInput.id = "dnf" + this.id;
    dnfInput.checked = data.DNF;
    dnfInput.onchange = () => {
      this.data.DNF = dnfInput.checked;
    };
    dnfCell.appendChild(dnfInput);
    this.element.appendChild(dnfCell);

    const dnsCell = document.createElement("td");
    const dnsInput = document.createElement("input");
    dnsInput.type = "checkbox";
    dnsInput.id = "dns" + this.id;
    dnsInput.checked = data.DNS;
    dnsInput.onchange = () => {
      this.data.DNS = dnsInput.checked;
    };
    dnsCell.appendChild(dnsInput);
    this.element.appendChild(dnsCell);

    const dqCell = document.createElement("td");
    const dqInput = document.createElement("input");
    dqInput.type = "checkbox";
    dqInput.id = "dq" + this.id;
    dqInput.checked = data.DQ;
    dqInput.onchange = () => {
      this.data.DQ = dqInput.checked;
    };
    dqCell.appendChild(dqInput);
    this.element.appendChild(dqCell);

    const athletes = document.getElementById("athletes");
    athletes.appendChild(this.element);
  }
}

function getAthleteId(athlete) {
  // athlete = { "_filename": "<athlete_id>.yaml" }
  if (athlete._filename.endsWith(".yaml")) {
    return athlete._filename.slice(0, -5);
  }
  throw (
    "Invalid athlete filename for athlete_id extraction: " + athlete._filename
  );
}

function chooseAthlete(callback) {
  // add a modal to choose an athlete
  const modal = document.createElement("div");
  modal.className = "modal";
  const modalContent = document.createElement("div");
  const modalTitle = document.createElement("h2");
  modalTitle.textContent = "Choose Athlete";
  modalContent.appendChild(modalTitle);

  const modalSearchbox = document.createElement("input");
  modalSearchbox.type = "text";
  modalSearchbox.id = "athlete_searchbox";
  modalSearchbox.placeholder = "Search for athlete...";
  modalContent.appendChild(modalSearchbox);

  const searchList = [];

  const modalList = document.createElement("div");
  for (const athlete_id in athlete_list) {
    const athleteButton = newAthleteForModal(athlete_id, (athlete_id) => {
      modal.remove();
      callback(athlete_id);
    });
    modalList.appendChild(athleteButton);
    searchList.push({
      athlete_id: athlete_id,
      name: athlete_list[athlete_id].name,
      button: athleteButton,
    });
  }

  const fuseOptions = {
    // isCaseSensitive: false,
    // includeScore: false,
    // shouldSort: true,
    // includeMatches: false,
    // findAllMatches: false,
    // minMatchCharLength: 1,
    // location: 0,
    // threshold: 0.6,
    // distance: 100,
    // useExtendedSearch: false,
    // ignoreLocation: false,
    // ignoreFieldNorm: false,
    // fieldNormWeight: 1,
    keys: ["name"],
  };

  const fuse = new Fuse(searchList, fuseOptions);

  modalSearchbox.onkeyup = () => {
    const filter = modalSearchbox.value.toLowerCase();
    const fuseResults = fuse.search(filter);
    const searchResults = [];
    for (const result of fuseResults) {
      searchResults.push(result.item.athlete_id);
    }
    for (const item of searchList) {
      if (searchResults.includes(item.athlete_id) || filter === "") {
        item.button.classList.remove("hidden");
      } else {
        item.button.classList.add("hidden");
      }
    }
  };

  modalContent.appendChild(modalList);
  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // focus modalSearchbox
  modalSearchbox.focus();
}

function newAthleteForModal(athlete_id, callback) {
  const athleteButton = document.createElement("button");
  athleteButton.className = "athlete_button";
  athleteButton.onclick = () => {
    callback(athlete_id);
  };
  athleteButton.style.backgroundColor =
    config.team_colours[athlete_list[athlete_id].team];
  // if the colour is too dark, make the text white
  const colour = athleteButton.style.backgroundColor;
  const rgb = colour.match(/\d+/g);
  const brightness = Math.round(
    (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) /
      1000
  );
  if (brightness < 125) {
    athleteButton.style.color = "white";
  }

  const athletePicture = document.createElement("img");
  athletePicture.src = "/athlete_photo/" + athlete_id;
  athletePicture.alt = athlete_list[athlete_id].name + "'s picture";
  athleteButton.appendChild(athletePicture);

  const athleteName = document.createElement("p");
  athleteName.textContent = athlete_list[athlete_id].name;
  athleteButton.appendChild(athleteName);

  return athleteButton;
}

function updateWarnings() {
  const athleteIdCounts = {};
  for (const result of editor.results) {
    if (athleteIdCounts[result.athlete_id] === undefined) {
      athleteIdCounts[result.athlete_id] = [];
    }
    athleteIdCounts[result.athlete_id].push(result);
  }

  // py: for athleteId, resultObjects in athleteIdCounts.items():
  for (const athleteId in athleteIdCounts) {
    const resultObjects = athleteIdCounts[athleteId];
    for (const resultObject of resultObjects) {
      if (resultObjects.length > 1) {
        resultObject.athleteButton.className = "athlete_button duplicated";
        resultObject.athleteButton.title = "Athlete is duplicated";
      } else {
        resultObjects[0].athleteButton.className = "athlete_button";
        resultObjects[0].athleteButton.title = "";
      }
    }
  }
  return athleteIdCounts;
}
