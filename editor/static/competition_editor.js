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

function resolve(path, obj = self, separator = ".") {
  var properties = Array.isArray(path) ? path : path.split(separator);
  return {
    get: function () {
      return properties.reduce((prev, curr) => prev && prev[curr], obj);
    },
    set: function (value) {
      for (const prop of properties.slice(0, -1)) {
        if (resolve(prop, obj).get() === undefined) {
          resolve(prop, obj).set({});
        }
      }
      properties.reduce((prev, curr, i, arr) => {
        if (i === arr.length - 1) {
          prev[curr] = value;
        }
        return prev[curr];
      }, obj);
    },
    delete: function () {
      properties.reduce((prev, curr, i, arr) => {
        if (i === arr.length - 1) {
          delete prev[curr];
        }
        return prev[curr];
      }, obj);
    },
  };
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

function addInstruction(instruction) {
  const instructionLi = document.createElement("li");
  instructionLi.innerHTML = instruction;
  document.getElementById("instructions").appendChild(instructionLi);
}

class CompetitionEditor {
  constructor(data, file_path) {
    this.data = data;
    this.results = [];
    this.columns = [];

    for (const key in data.results) {
      const r = new Result(key, data.results[key]);
      this.results.push(r);
    }

    const changeCompetitorTypeButton = document.createElement("button");
    if (this.data.competitor_type === "individual") {
      changeCompetitorTypeButton.innerHTML = "Change to Team";
    } else {
      changeCompetitorTypeButton.innerHTML = "Change to Individual";
    }

    changeCompetitorTypeButton.onclick = (e) => {
      if (this.data.competitor_type === "individual") {
        this.data.competitor_type = "team";
      } else {
        this.data.competitor_type = "individual";
      }
      this.save();
    };

    document.getElementById("header").appendChild(changeCompetitorTypeButton);

    this.appendColumn({
      name: "Athlete",
      field: null,
      type: "athlete_select",
    });

    if (this.data.type === "race") {
      this.appendColumn({
        name: "Heat",
        field: "heat",
        type: "NumberField",
        min: 1,
      });

      this.appendColumn({
        name: "Place",
        field: "place",
        type: "NumberField",
        min: 1,
      });

      // sort athletes by heat and place
      this.results.sort((a, b) => {
        console.log(a.data.heat, b.data.heat, a.data.place, b.data.place);
        return a.data.heat - b.data.heat || a.data.place - b.data.place;
      });

      this.appendColumn({
        name: "Finish Time",
        field: "finish_time",
        type: "DurationField",
      });
    } else if (this.data.type === "high_jump") {
      addInstruction(
        "Enter 'f' for failed attempts and 's' for successful attempts. " +
        "For example, 'ffs' would indicate two failed attempts then one successful attempt."
      );

      addInstruction(
        "If an athlete did not attempt a jump, leave the field blank."
      );

      addInstruction(
        "Only enter 3 attempts. If an athlete only attempted i.e., 2 jumps, only enter 2 characters."
      );

      if (this.data.heights === undefined) {
        this.data.heights = [];
      }

      for (const key in data.results) {
        for (const height in data.results[key]["heights"]) {
          if (!this.data.heights.includes(height)) {
            this.data.heights.push(height);
          }
        }
      }
      // de-duplicate the heights
      this.data.heights = [...new Set(this.data.heights)];

      this.data.heights.sort((a, b) => a - b);
      for (const column of this.data.heights) {
        this.appendColumn({
          name: column + " mm",
          field: ["heights", column],
          type: "HighJumpAttemptsField",
        });
      }

      const addHeightButton = document.createElement("button");
      addHeightButton.innerHTML = "Add Height";
      addHeightButton.onclick = (e) => {
        const height = prompt("Enter the height in mm");
        if (height !== null) {
          // add an empty list to each athlete's heights
          for (const result of this.results) {
            result.data.heights[height] = [];
          }
          this.appendColumn({
            name: height + " mm",
            field: ["heights", height],
            type: "HighJumpAttemptsField",
          });
          // add to the editors .heights
          this.data.heights.push(Number(height));
        }
      };
      document.getElementById("header").appendChild(addHeightButton);
    }

    addInstruction(
      "NB: The place field is only used by the editor, it is not used in results calculations."
    );

    for (const checkbox_type of ["DNF", "DNS", "DQ"]) {
      this.appendColumn({
        name: checkbox_type,
        field: checkbox_type,
        type: "checkbox",
      });
    }

    this.appendColumn({
      name: "",
      field: null,
      type: "remove_button",
    });

    // add the results to the table
    for (const result of this.results) {
      document.getElementById("tableBody").appendChild(result.DOMObject);
    }

    document
      .getElementById("newResult")
      .addEventListener("click", this.addResult.bind(this));

    document
      .getElementById("save")
      .addEventListener("click", this.save.bind(this));

    // listen for (CTRL or CMD) + S to save
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        this.save();
      }
    });
  }
  appendColumn(column) {
    this.columns.push(column);
    const tableHeaderRow = document.getElementById("tableHeaderRow");
    const th = document.createElement("th");
    th.innerHTML = column.name;
    tableHeaderRow.appendChild(th);

    for (const result of this.results) {
      console.log(column);
      result.appendColumn(column);
    }
  }
  addResult(e) {
    const athlete = prompt("Enter the athlete's id");
    if (athlete !== null) {
      this.data.results[athlete] = {};

      if (this.data.type === "race") {
        let maximumHeat = 1;
        for (const result of this.results) {
          if (
            Number(result.data.heat) !== undefined &&
            Number(result.data.heat) > maximumHeat
          ) {
            maximumHeat = Number(result.data.heat);
          }
        }

        if (e.shiftKey) {
          maximumHeat += 1;
        }

        let maximumPlace = 0;
        for (const result of this.results) {
          if (
            Number(result.data.place) !== undefined &&
            Number(result.data.heat) === maximumHeat
          ) {
            if (Number(result.data.place) > maximumPlace) {
              maximumPlace = Number(result.data.place);
            }
          }
        }

        this.data.results[athlete]["heat"] = maximumHeat;
        this.data.results[athlete]["place"] = maximumPlace + 1;
      }

      const r = new Result(athlete, this.data.results[athlete]);
      this.results.push(r);
      document.getElementById("tableBody").appendChild(r.DOMObject);
      for (const column of this.columns) {
        r.appendColumn(column);
      }
    }
  }
  getData() {
    // tidy the heights
    for (const key in this.data.results) {
      for (const height in this.data.results[key]["heights"]) {
        if (!this.data.heights.includes(height)) {
          this.data.heights.push(height);
        }
      }
    }
    // de-duplicate the heights
    this.data.heights = [...new Set(this.data.heights)];
    this.data.heights.sort((a, b) => a - b);

    return this.data;
  }
  save() {
    // save the data to the server
    console.log(this.data);
    const data = editor.getData();
    fetch(window.location, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        if (response.ok) {
          window.location.reload();
        } else {
          alert("Failed to save");
          console.log(response);
        }
      })
      .catch((error) => {
        alert("Failed to save");
        console.log(error);
      });
  }
}

class Result {
  constructor(athlete_id, data, DOMObject = null) {
    this.athlete_id = athlete_id;
    this.data = data;
    if (DOMObject !== null) {
      this.DOMObject = DOMObject;
    } else {
      this.DOMObject = document.createElement("tr");
    }
  }
  appendColumn(column) {
    if (column.type === "athlete_select") {
      this.DOMObject.appendChild(new AthleteSelect(this.athlete_id).DOMObject);
    } else if (column.type === "DurationField") {
      this.DOMObject.appendChild(
        new DurationField(resolve(column.field, this.data)).DOMObject
      );
    } else if (column.type === "NumberField") {
      this.DOMObject.appendChild(
        new NumberField(
          resolve(column.field, this.data),
          column.min,
          column.max
        ).DOMObject
      );
    } else if (column.type === "HighJumpAttemptsField") {
      this.DOMObject.appendChild(
        new HighJumpAttemptsField(resolve(column.field, this.data)).DOMObject
      );
    } else if (column.type === "checkbox") {
      this.DOMObject.appendChild(
        new CheckboxField(resolve(column.field, this.data)).DOMObject
      );
    } else if (column.type === "remove_button") {
      this.DOMObject.appendChild(new RemoveButton(this.athlete_id).DOMObject);
    } else {
      const dummyTd = document.createElement("td");
      dummyTd.innerHTML = "Not Implemented";
      this.DOMObject.appendChild(dummyTd);
    }
  }
}

function fieldKeyDownHandler(e) {
  /* Enter will advance to the same field in the next row             \
  |  Shift + Enter will advance to the same field in the previous row |
  \  This should wrap if the current row is the first or last row    */

  if (e.key === "Enter") {
    let newSelection;
    if (e.shiftKey) {
      newSelection = e.target.parentElement.parentElement.previousSibling;
      if (newSelection === null || newSelection.tagName !== "TR") {
        // get the last TR in the table
        const rows =
          e.target.parentElement.parentElement.parentElement.getElementsByTagName(
            "TR"
          );
        newSelection = rows[rows.length - 1];
      }
    } else {
      newSelection = e.target.parentElement.parentElement.nextSibling;
      if (newSelection === null || newSelection.tagName !== "TR") {
        // get the first TR in the table
        const rows =
          e.target.parentElement.parentElement.parentElement.getElementsByTagName(
            "TR"
          );
        newSelection = rows[0];
      }
    }

    // get the index of the current cell
    const index = Array.from(
      e.target.parentElement.parentElement.children
    ).indexOf(e.target.parentElement);

    // get the next cell
    const nextCell = newSelection.children[index];
    nextCell.children[0].focus();
  }
}

class AthleteSelect {
  constructor(athlete_id) {
    this.athlete_id = athlete_id;
    this.DOMObject = document.createElement("td");
    const changeAthleteButton = document.createElement("button");
    changeAthleteButton.innerHTML = athlete_id;
    changeAthleteButton.onclick = (e) => {
      const new_athlete_id = prompt("Enter the athlete's id");
      if (!(new_athlete_id === null || new_athlete_id === "")) {
        if (editor.data.results[new_athlete_id] === undefined) {
          editor.data.results[new_athlete_id] =
            editor.data.results[this.athlete_id];
          delete editor.data.results[this.athlete_id];
          // delete the result object from the editor.results array
          editor.results = editor.results.filter(
            (result) => result.athlete_id !== this.athlete_id
          );

          const r = new Result(
            new_athlete_id,
            editor.data.results[new_athlete_id]
          );
          editor.results.push(r);
          // replace the old DOM object with the new one
          this.DOMObject.innerHTML = "";
          this.DOMObject.parentElement.replaceWith(r.DOMObject);
          for (const column of editor.columns) {
            r.appendColumn(column);
          }
        } else {
          if (confirm("Do you wish to swap these athletes?")) {
            const this_athlete_data = structuredClone(
              editor.data.results[this.athlete_id]
            );
            const other_athlete_data = structuredClone(
              editor.data.results[new_athlete_id]
            );

            editor.data.results[this.athlete_id] = other_athlete_data;
            editor.data.results[new_athlete_id] = this_athlete_data;

            const this_athlete_DOMObject = editor.results.filter(
              (result) => result.athlete_id === this.athlete_id
            )[0].DOMObject;
            const other_athlete_DOMObject = editor.results.filter(
              (result) => result.athlete_id === new_athlete_id
            )[0].DOMObject;

            editor.results = editor.results.filter(
              (result) =>
                result.athlete_id !== this.athlete_id &&
                result.athlete_id !== new_athlete_id
            );

            other_athlete_DOMObject.innerHTML = "";
            const this_DOMObject_new = new Result(
              this.athlete_id,
              other_athlete_data,
              other_athlete_DOMObject
            );
            for (const column of editor.columns) {
              this_DOMObject_new.appendColumn(column);
            }
            editor.results.push(this_DOMObject_new);

            this_athlete_DOMObject.innerHTML = "";
            const other_DOMObject_new = new Result(
              new_athlete_id,
              this_athlete_data,
              this_athlete_DOMObject
            );
            for (const column of editor.columns) {
              other_DOMObject_new.appendColumn(column);
            }
            editor.results.push(other_DOMObject_new);
          }
        }
      } else {
        alert("Please enter an Athlete ID");
      }
    };
    this.DOMObject.appendChild(changeAthleteButton);
  }
}

class RemoveButton {
  constructor(athlete_id) {
    this.athlete_id = athlete_id;
    this.DOMObject = document.createElement("td");
    const deleteAthleteButton = document.createElement("button");
    deleteAthleteButton.innerHTML = "Delete";
    deleteAthleteButton.onclick = (e) => {
      // delete the DOMObject
      this.DOMObject.parentElement.remove();
      // delete the result in the data
      delete editor.data.results[this.athlete_id];
      // delete the result object from the editor.results array
      editor.results = editor.results.filter(
        (result) => result.athlete_id !== this.athlete_id
      );
    };
    this.DOMObject.appendChild(deleteAthleteButton);
  }
}

class DurationField {
  constructor(value) {
    this.value = value;
    this.DOMObject = document.createElement("td");
    const inputBox = document.createElement("input");
    inputBox.type = "text";
    const raw_value = value.get();
    if (raw_value === undefined) {
      inputBox.value = "";
    } else {
      inputBox.value = millisecondsToHhmmss(raw_value);
    }
    inputBox.onchange = (e) => {
      if (e.target.value === "") {
        value.delete();
      } else {
        value.set(hhmmssToMilliseconds(e.target.value));
      }
    };

    inputBox.onkeydown = fieldKeyDownHandler;

    this.DOMObject.appendChild(inputBox);
  }
}

class NumberField {
  constructor(value, min = null, max = null) {
    this.value = value;
    this.DOMObject = document.createElement("td");
    const inputBox = document.createElement("input");
    inputBox.type = "number";
    if (min !== null) {
      inputBox.min = min;
    }
    if (max !== null) {
      inputBox.max = max;
    }
    inputBox.value = value.get();
    inputBox.onchange = (e) => {
      value.set(Number(e.target.value));
    };
    this.DOMObject.appendChild(inputBox);
  }
}

class HighJumpAttemptsField {
  constructor(value) {
    this.value = value;
    this.DOMObject = document.createElement("td");
    // convert false, false, true to ffs (failed, failed, success)
    const raw_value = this.value.get();
    if (raw_value !== undefined) {
      this.appendInputBox(raw_value);
    } else {
      this.appendCreateInputButton();
    }
  }

  appendCreateInputButton() {
    const createInputButton = document.createElement("button");
    createInputButton.innerHTML = "Create Input";
    createInputButton.onclick = (e) => {
      this.value.set([]);
      this.appendInputBox(this.value.get());
      e.target.remove();
    };
    this.DOMObject.appendChild(createInputButton);
  }

  appendInputBox(raw_value) {
    const inputBox = document.createElement("input");
    inputBox.type = "text";
    inputBox.value = raw_value.map((v) => (v ? "s" : "f")).join("");
    inputBox.onchange = (e) => {
      // validate the input is only f and s and a maximum of 3 characters
      if (
        (/^[fs]+$/.test(e.target.value) ||
          confirm(
            "The current field contains incorrect characters. Any characters other than 'f' and 's' will be treated as 'f'. Continue anyway?"
          )) &&
        (e.target.value.length <= 3 ||
          confirm(
            "The current field contains more than 3 characters. Continue anyway?"
          )) &&
        ((e.target.value.match(/s/g) || []).length <= 1 ||
          confirm(
            "The current field contains more than 1 successful attempt. Continue anyway?"
          )) &&
        (e.target.value[e.target.value.length - 1] === "s" ||
          !e.target.value.includes("s") ||
          confirm(
            "The current field contains an unsuccessful attempt as the last. Continue anyway?"
          ))
      ) {
        this.value.set(
          e.target.value.split("").map((v) => (v === "s" ? true : false))
        );
      } else {
        e.target.value = raw_value.map((v) => (v ? "s" : "f")).join("");
      }
    };
    this.DOMObject.appendChild(inputBox);
    const removeValueButton = document.createElement("button");
    removeValueButton.innerHTML = "Remove";
    removeValueButton.onclick = (e) => {
      this.value.delete();
      this.DOMObject.innerHTML = "";
      this.appendCreateInputButton();
    };
    this.DOMObject.appendChild(removeValueButton);
  }
}

class CheckboxField {
  constructor(value) {
    this.value = value;
    this.DOMObject = document.createElement("td");
    this.checkbox = document.createElement("input");
    this.checkbox.type = "checkbox";

    if (value.get() === true) {
      this.checkbox.checked = true;
    }

    this.checkbox.onchange = (e) => {
      if (this.checkbox.checked === true) {
        this.value.set(true);
      } else {
        this.value.delete();
      }
    };

    this.DOMObject.appendChild(this.checkbox);
  }
}
