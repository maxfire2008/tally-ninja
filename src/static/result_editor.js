/* example usage:
/  data = {'type': 'race', 'name': 'Duathlon Short Course', 'distance': 'short_course', 'date': datetime.date(2023, 7, 1), 'results': {'donald_trump': {'finish_time': 3473430}, 'joe_biden': {'finish_time': 3382120}, 'kamala_harris': {'finish_time': 2537320}, 'hillary_clinton': {'finish_time': 2964450}, 'mitch_mcconnell': {'DNF': True}, 'nancy_pelosi': {'finish_time': 2172180}, 'bernie_sanders': {'finish_time': 9123850}, 'elizabeth_warren': {'finish_time': 2172180}}, '_filepath': '..\\sample_data\\results\\duathlon\\2023-07-duathlon-short.yaml', '_filename': '2023-07-duathlon-short.yaml'}
/  result_editor = new ResultEditor(data); */

var last_id = 0;

function new_id() {
  last_id += 1;
  return last_id;
}

class ResultEditor {
  constructor(data) {
    this.data = data;
    this.changed_data = {};
    var header = document.getElementById("header");

    var nameDiv = document.createElement("div");
    var nameLabel = document.createElement("label");
    nameLabel.htmlFor = "name";
    nameLabel.textContent = "Name";
    var nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.id = "name";
    nameInput.value = data.name;
    nameInput.onchange = () => {
      this.changed_data.name = nameInput.value;
    };
    nameDiv.appendChild(nameLabel);
    nameDiv.appendChild(nameInput);
    header.appendChild(nameDiv);

    var distanceDiv = document.createElement("div");
    var distanceLabel = document.createElement("label");
    distanceLabel.htmlFor = "distance";
    distanceLabel.textContent = "Distance";
    var distanceInput = document.createElement("input");
    distanceInput.type = "text";
    distanceInput.id = "distance";
    distanceInput.value = data.distance;
    distanceInput.onchange = () => {
      this.changed_data.distance = distanceInput.value;
    };
    distanceDiv.appendChild(distanceLabel);
    distanceDiv.appendChild(distanceInput);
    header.appendChild(distanceDiv);

    var dateDiv = document.createElement("div");
    var dateLabel = document.createElement("label");
    dateLabel.htmlFor = "date";
    dateLabel.textContent = "Date";
    var dateInput = document.createElement("input");
    dateInput.type = "date";
    dateInput.id = "date";
    dateInput.value = data.date;
    dateInput.onchange = () => {
      this.changed_data.date = dateInput.value;
    };
    dateDiv.appendChild(dateLabel);
    dateDiv.appendChild(dateInput);
    header.appendChild(dateDiv);

    this.results = [];
    for (var athlete_id in data.results) {
      this.results.push(new Result(athlete_id, data.results[athlete_id]));
    }
  }
}

class Result {
  constructor(athlete_id, data) {
    this.athlete_id = athlete_id;
    this.data = data;
    this.id = new_id();
    this.changed_data = {};

    this.element = document.createElement("tr");
    this.element.className = "result";

    var athleteCell = document.createElement("td");
    var athleteButton = document.createElement("button");
    athleteButton.id = "athlete" + this.id;
    athleteButton.textContent = athlete_id;
    athleteButton.onclick = () => {
      this.athlete_id = chooseAthlete();
    };
    athleteCell.appendChild(athleteButton);
    this.element.appendChild(athleteCell);

    var finishTimeCell = document.createElement("td");
    var finishTimeInput = document.createElement("input");
    finishTimeInput.type = "text";
    finishTimeInput.id = "finish_time" + this.id;
    finishTimeInput.value = data.finish_time;
    finishTimeInput.onchange = () => {
      this.changed_data.finish_time = finishTimeInput.value;
    };
    finishTimeCell.appendChild(finishTimeInput);
    this.element.appendChild(finishTimeCell);

    var dnfCell = document.createElement("td");
    var dnfInput = document.createElement("input");
    dnfInput.type = "checkbox";
    dnfInput.id = "dnf" + this.id;
    dnfInput.checked = data.DNF;
    dnfInput.onchange = () => {
      this.changed_data.DNF = dnfInput.checked;
    };
    dnfCell.appendChild(dnfInput);
    this.element.appendChild(dnfCell);

    var dnsCell = document.createElement("td");
    var dnsInput = document.createElement("input");
    dnsInput.type = "checkbox";
    dnsInput.id = "dns" + this.id;
    dnsInput.checked = data.DNS;
    dnsInput.onchange = () => {
      this.changed_data.DNS = dnsInput.checked;
    };
    dnsCell.appendChild(dnsInput);
    this.element.appendChild(dnsCell);

    var dqCell = document.createElement("td");
    var dqInput = document.createElement("input");
    dqInput.type = "checkbox";
    dqInput.id = "dq" + this.id;
    dqInput.checked = data.DQ;
    dqInput.onchange = () => {
      this.changed_data.DQ = dqInput.checked;
    };
    dqCell.appendChild(dqInput);
    this.element.appendChild(dqCell);

    var athletes = document.getElementById("athletes");
    athletes.appendChild(this.element);
  }
}

function chooseAthlete() {
  // add a modal to choose an athlete
  var modal = document.createElement("div");
  modal.className = "modal";
  var modalContent = document.createElement("div");
  var modalTitle = document.createElement("h2");
  modalTitle.textContent = "Choose Athlete";
  modalContent.appendChild(modalTitle);
  var modalList = document.createElement("div");
  for (var athlete of athlete_list) {
    var athleteButton = document.createElement("button");
    athleteButton.textContent = athlete.name;
    athleteButton.onclick = () => {
      alert("athlete clicked");
    };
    modalList.appendChild(athleteButton);
  }
  modalContent.appendChild(modalList);
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
}
