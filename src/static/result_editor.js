"use strict";
/* example usage:
/  const data = {'type': 'race', 'name': 'Duathlon Short Course', 'distance': 'short_course', 'date': datetime.date(2023, 7, 1), 'results': {'donald_trump': {'finish_time': 3473430}, 'joe_biden': {'finish_time': 3382120}, 'kamala_harris': {'finish_time': 2537320}, 'hillary_clinton': {'finish_time': 2964450}, 'mitch_mcconnell': {'DNF': True}, 'nancy_pelosi': {'finish_time': 2172180}, 'bernie_sanders': {'finish_time': 9123850}, 'elizabeth_warren': {'finish_time': 2172180}}, '_filepath': '..\\sample_data\\results\\duathlon\\2023-07-duathlon-short.yaml', '_filename': '2023-07-duathlon-short.yaml'}
/  const athlete_list = {"bernie_sanders":{"_filename":"bernie_sanders.yaml","_filepath":"../sample_data/athletes/bernie_sanders.yaml","dob":"Mon, 08 Sep 1941 00:00:00 GMT","gender":"male","name":"Bernie Sanders","team":"blue"}, "kamala_harris":{"_filename":"kamala_harris.yaml","_filepath":"../sample_data/athletes/kamala_harris.yaml","dob":"Tue, 20 Oct 1964 00:00:00 GMT","gender":"female","name":"Kamala Harris","team":"blue"}}
/  const result_editor = new ResultEditor(data);
*/

localStorage.openpages = Date.now();
var onLocalStorageEvent = function (e) {
  if (e.key == "openpages") {
    // Listen if anybody else is opening the same page!
    localStorage.page_available = Date.now();
  }
  if (e.key == "page_available") {
    alert("Another Tally Ninja tab is open! Proceed with caution!");
  }
};
window.addEventListener("storage", onLocalStorageEvent, false);

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
    this.modal = null;

    this.data = data;
    const header = document.getElementById("header");

    if (
      data.competitor_type === "individual" ||
      data.competitor_type === undefined
    ) {
      this.competitor_type = "individual";
      const tableHeaderCell = document.createElement("th");
      tableHeaderCell.textContent = "Athlete";
      document.getElementById("tableHeaderRow").appendChild(tableHeaderCell);
    } else if (data.competitor_type === "team") {
      this.competitor_type = "team";
      const tableHeaderCell = document.createElement("th");
      tableHeaderCell.textContent = "Team";
      document.getElementById("tableHeaderRow").appendChild(tableHeaderCell);
    } else {
      document.getElementById("save").remove();
      document.body.textContent =
        "Invalid competitor type: " + data.competitor_type;
      throw new Error("Invalid competitor type: " + data.competitor_type);
    }

    if (data.type === "race") {
      this.mainValue = "finish_time";
      const tableHeaderCell = document.createElement("th");
      tableHeaderCell.textContent = "Finish Time";
      document.getElementById("tableHeaderRow").appendChild(tableHeaderCell);
    } else if (data.type === "bonus_points") {
      this.mainValue = "points";
      const tableHeaderCell = document.createElement("th");
      tableHeaderCell.textContent = "Points";
      document.getElementById("tableHeaderRow").appendChild(tableHeaderCell);
    } else {
      document.getElementById("save").remove();
      document.body.textContent = "Invalid result type: " + data.type;
      throw new Error("Invalid result type: " + data.type);
    }

    const nameDiv = document.createElement("div");
    const nameLabel = document.createElement("label");
    nameLabel.htmlFor = "name";
    nameLabel.textContent = "Name";
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.id = "name";
    if (data.name === undefined) {
      nameInput.value = "";
    } else {
      nameInput.value = data.name;
    }
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
    if (data.distance === undefined) {
      distanceInput.value = "";
    } else {
      distanceInput.value = data.distance;
    }
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
    dateInput.type = "datetime-local";
    dateInput.id = "date";
    dateInput.value = data.date;
    dateInput.onchange = () => {
      this.data.date = dateInput.value;
    };
    dateDiv.appendChild(dateLabel);
    dateDiv.appendChild(dateInput);
    header.appendChild(dateDiv);

    this.results = [];
    // sort data.results by this.sorting_key
    const athlete_ids = Object.keys(data.results);
    athlete_ids.sort((a, b) => {
      if (data.results[a][this.mainValue] === undefined) {
        return 1;
      }
      if (data.results[b][this.mainValue] === undefined) {
        return -1;
      }
      return data.results[a][this.mainValue] - data.results[b][this.mainValue];
    });

    for (const athlete_id of athlete_ids) {
      this.results.push(
        new Result(athlete_id, data.results[athlete_id], this.mainValue)
      );
    }

    const new_result = document.getElementById("new_result");
    new_result.onclick = () => {
      this.new_result();
    };

    const save = document.getElementById("save");
    save.onclick = () => {
      this.save();
    };

    // keyboard shortcuts (ctrl+s to save, ctrl+enter to add new result)
    // for mac, use metaKey instead of ctrlKey because Apple is weird

    if (navigator.userAgent.includes("Macintosh")) {
      this.specialKey = "metaKey";
    } else {
      this.specialKey = "ctrlKey";
    }

    document.onkeydown = (e) => {
      if (e[this.specialKey] && e.key === "s") {
        e.preventDefault();
        this.save();
      } else if (e[this.specialKey] && e.key === "Enter") {
        e.preventDefault();
        this.new_result();
      } else if (e.key === "Escape") {
        if (this.modal !== null) {
          this.modal.remove();
          this.modal = null;
        }
      } else if (e.key === "Enter" && this.modal !== null) {
        this.modal.selectFirst();
      }
    };
  }

  new_result() {
    this.modal = chooseAthlete((athlete_id) => {
      this.modal = null;
      this.results.push(new Result(athlete_id, {}, this.mainValue));
      // set focus to the new result's this.sorting_key input
      const mainValueInput =
        this.results[this.results.length - 1].mainValueInput.focus();
      updateWarnings();
    });
  }

  save() {
    const data = this.data;
    data.results = {};
    for (const result of this.results) {
      if (!result.deleted) {
        data.results[result.athlete_id] = result.data;
      }
    }
    console.log(data);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/save_result");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(data));
    xhr.onloadend = () => {
      if (xhr.status !== 200) {
        alert("Error saving result: " + xhr.status + " " + xhr.statusText);
      }
    };
  }
}

class Result {
  constructor(athlete_id, data, mainValue) {
    this.mainValue = mainValue;
    this.athlete_id = athlete_id;
    this.data = data;
    this.id = new_id();

    this.element = document.createElement("tr");
    this.element.className = "result";

    const athleteCell = document.createElement("td");
    this.athleteButton = document.createElement("button");
    this.athleteButton.id = "athlete" + this.id;
    if (editor.competitor_type === "individual") {
      this.athleteButton.textContent = athlete_list[athlete_id].name;
    } else if (editor.competitor_type === "team") {
      this.athleteButton.textContent = config.teams[athlete_id].name;
    }
    this.athleteButton.onclick = () => {
      this.modal = chooseAthlete((athlete_id) => {
        this.modal = null;
        if (editor.competitor_type === "individual") {
          this.athleteButton.textContent = athlete_list[athlete_id].name;
        } else if (editor.competitor_type === "team") {
          this.athleteButton.textContent = config.teams[athlete_id].name;
        }
        this.athlete_id = athlete_id;
        updateWarnings();
      });
    };
    athleteCell.appendChild(this.athleteButton);
    this.element.appendChild(athleteCell);

    const mainValueCell = document.createElement("td");
    this.mainValueInput = document.createElement("input");
    this.mainValueInput.type = "text";
    this.mainValueInput.id = this.mainValue + this.id;
    if (data[this.mainValue] === undefined) {
      this.mainValueInput.value = "";
    } else {
      if (data.type === "race") {
        this.mainValueInput.value = millisecondsToHhmmss(data[this.mainValue]);
      } else {
        this.mainValueInput.value = data[this.mainValue];
      }
    }
    this.mainValueInput.onchange = () => {
      if (data.type === "race") {
        this.data[this.mainValue] = hhmmssToMilliseconds(
          this.mainValueInput.value
        );
      } else {
        this.data[this.mainValue] = this.mainValueInput.value;
      }
    };
    mainValueCell.appendChild(this.mainValueInput);
    this.element.appendChild(mainValueCell);

    if (editor.data.type === "bonus_points") {
      const reasonCell = document.createElement("td");
      const reasonInput = document.createElement("input");
      reasonInput.type = "text";
      reasonInput.id = "reason" + this.id;
      if (data.reason === undefined) {
        reasonInput.value = "";
      } else {
        reasonInput.value = data.reason;
      }
      reasonInput.onchange = () => {
        this.data.reason = reasonInput.value;
      };
      reasonCell.appendChild(reasonInput);
      this.element.appendChild(reasonCell);
    }

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

    const deleteButtonCell = document.createElement("td");
    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.onclick = () => {
      this.deleted = true;
      this.element.remove();
    };
    deleteButtonCell.appendChild(deleteButton);
    this.element.appendChild(deleteButtonCell);

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

  const cancelButton = document.createElement("button");
  cancelButton.textContent = "Cancel";
  cancelButton.onclick = () => {
    modal.remove();
  };
  modalContent.appendChild(cancelButton);

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
  if (editor.competitor_type === "individual") {
    for (const athlete_id in athlete_list) {
      const athleteButton = newAthleteForModal(
        athlete_id,
        (athlete_id) => {
          modal.remove();
          localStorage.setItem("latest_athlete_id", athlete_id);
          callback(athlete_id);
        },
        "individual"
      );
      modalList.appendChild(athleteButton);
      searchList.push({
        athlete_id: athlete_id,
        name: athlete_list[athlete_id].name,
        button: athleteButton,
      });
    }
  } else if (editor.competitor_type === "team") {
    for (const team_id in config.teams) {
      const teamButton = newAthleteForModal(
        team_id,
        (team_id) => {
          modal.remove();
          callback(team_id);
        },
        "team"
      );
      modalList.appendChild(teamButton);
      searchList.push({
        athlete_id: team_id,
        name: config.teams[team_id].name,
        button: teamButton,
      });
    }
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

    modalList.innerHTML = "";
    if (filter === "") {
      for (const athlete_id in athlete_list) {
        const athleteButton = newAthleteForModal(athlete_id, (athlete_id) => {
          modal.remove();
          callback(athlete_id);
        });
        modalList.appendChild(athleteButton);
      }
    } else {
      const fuseResults = fuse.search(filter);
      const searchResults = [];
      for (const result of fuseResults) {
        const athleteButton = newAthleteForModal(
          result.item.athlete_id,
          (athlete_id) => {
            modal.remove();
            callback(athlete_id);
          }
        );
        modalList.appendChild(athleteButton);
      }
    }
  };

  modalContent.appendChild(modalList);
  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // focus modalSearchbox
  modalSearchbox.focus();

  return {
    remove: () => {
      modal.remove();
    },
    selectFirst: () => {
      // like clicking the first button in the list / only allow this if the searchbox has something in it
      if (modalSearchbox.value !== "") {
        modalList.firstChild.click();
      }
    },
  };
}

function newAthleteForModal(athlete_id, callback, competitor_type) {
  const athleteButton = document.createElement("button");
  athleteButton.className = "athlete_button";
  athleteButton.onclick = () => {
    callback(athlete_id);
  };
  if (competitor_type === "individual") {
    athleteButton.style.backgroundColor =
      config.teams[athlete_list[athlete_id].team].colour;
  } else if (competitor_type === "team") {
    athleteButton.style.backgroundColor = config.teams[athlete_id].colour;
  }
  // if the colour is too dark, make the text white
  const colour = athleteButton.style.backgroundColor;
  const rgb = colour.match(/\d+/g);
  if (rgb !== null) {
    const brightness = Math.round(
      (parseInt(rgb[0]) * 299 +
        parseInt(rgb[1]) * 587 +
        parseInt(rgb[2]) * 114) /
        1000
    );
    if (brightness < 125) {
      athleteButton.style.color = "white";
    }
  }

  const athletePicture = document.createElement("img");
  if (competitor_type === "individual") {
    athletePicture.src = "/athlete_photo/" + athlete_id;
  } else if (competitor_type === "team") {
    athletePicture.src = "/team_photo/" + athlete_id;
  }
  if (competitor_type === "individual") {
    athletePicture.alt = athlete_list[athlete_id].name + "'s picture";
  } else if (competitor_type === "team") {
    athletePicture.alt = config.teams[athlete_id].name + "'s picture";
  }

  athleteButton.appendChild(athletePicture);

  const athleteName = document.createElement("p");
  if (competitor_type === "individual") {
    athleteName.textContent = athlete_list[athlete_id].name;
  } else if (competitor_type === "team") {
    athleteName.textContent = config.teams[athlete_id].name;
  }
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
