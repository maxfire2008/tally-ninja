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

function resolve(path, obj = self, separator = ".") {
  var properties = Array.isArray(path) ? path : path.split(separator);
  return properties.reduce((prev, curr) => prev?.[curr], obj);
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

class CompetitionEditor {
  constructor(data) {
    this.data = data;
    this.results = [];
    for (const key in data.results) {
      const r = new Result(key, data.results[key]);
      this.results.push(r);
      document.getElementById("tableBody").appendChild(r.DOMObject);
    }

    this.appendColumn({ name: "Name", field: "name", type: "name_display" });

    if (this.data.type === "race") {
      this.appendColumn({
        name: "Finish Time",
        field: "finish_time",
        type: "duration",
      });
    } else if (this.data.type === "high_jump") {
      let hj_columns = [];
      for (const key in data.results) {
        for (const height in data.results[key]["heights"]) {
          if (!hj_columns.includes(height)) {
            hj_columns.push(height);
          }
        }
      }
      hj_columns.sort();
      for (const column of hj_columns) {
        this.appendColumn({
          name: column + " mm",
          field: ["heights", column],
          type: "high_jump_attempts",
        });
      }
    }

    for (const result of this.results) {
      result.appendColumn({
        name: "Remove",
        type: "remove_button",
        value: () => {
          delete this.data.results[result.athlete_id];
        },
      });
    }
  }
  appendColumn(column) {
    const tableHeaderRow = document.getElementById("tableHeaderRow");
    const th = document.createElement("th");
    th.innerHTML = column.name;
    tableHeaderRow.appendChild(th);

    for (const result of this.results) {
      console.log(column);
      result.appendColumn(column);
    }
  }
}

class Result {
  constructor(athlete_id, data) {
    this.athlete_id = athlete_id;
    this.data = data;
    this.DOMObject = document.createElement("tr");
  }
  appendColumn(column) {
    if (column.type === "name_display") {
      this.DOMObject.appendChild(
        this.DOMObject.appendChild(
          new Cell(this.athlete_id, "text_display").DOMObject
        )
      );
    } else if (column.type === "remove_button") {
      this.DOMObject.appendChild(
        new Cell(column.value, "remove_button").DOMObject
      );
    } else {
      console.log(resolve(column.field, this.data), column.field, this.data);
      this.DOMObject.appendChild(
        new Cell(resolve(column.field, this.data), column.type).DOMObject
      );
    }
  }
}

class Cell {
  constructor(value, type) {
    this.value = value;
    this.type = type;
    this.DOMObject = document.createElement("td");
    if (this.type === "text_display") {
      this.DOMObject.innerHTML = this.value;
    } else if (this.type === "high_jump_attempts") {
      const inputBox = document.createElement("input");
      inputBox.type = "text";
      // convert false, false, true to ffs (failed, failed, success)
      inputBox.value = this.value.map((v) => (v ? "s" : "f")).join("");
      inputBox.onchange = (e) => {
        this.value = e.target.value
          .split("")
          .map((v) => (v === "s" ? true : false));
      };
      this.DOMObject.appendChild(inputBox);
    } else if (this.type === "remove_button") {
      const button = document.createElement("button");
      button.innerHTML = "Remove";
      button.onclick = () => {
        this.value();
        this.DOMObject.parentElement.remove();
      };
      this.DOMObject.appendChild(button);
    } else {
      this.DOMObject.innerHTML = JSON.stringify(this.value);
    }
  }
}
