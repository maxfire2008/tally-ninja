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
    nameLabel.innerHTML = "Name";
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
    distanceLabel.innerHTML = "Distance";
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
    dateLabel.innerHTML = "Date";
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

    this.element = document.createElement("div");
    this.element.className = "result";

    var athleteDiv = document.createElement("div");
    var athleteLabel = document.createElement("label");
    athleteLabel.htmlFor = "athlete" + this.id;
    athleteLabel.innerHTML = "Athlete";
    var athleteInput = document.createElement("input");
    athleteInput.type = "text";
    athleteInput.id = "athlete" + this.id;
    athleteInput.value = athlete_id;
    athleteInput.onchange = () => {
      this.athlete_id = athleteInput.value;
    };
    athleteDiv.appendChild(athleteLabel);
    athleteDiv.appendChild(athleteInput);
    this.element.appendChild(athleteDiv);

    var finishTimeDiv = document.createElement("div");
    var finishTimeLabel = document.createElement("label");
    finishTimeLabel.htmlFor = "finish_time" + this.id;
    finishTimeLabel.innerHTML = "Finish Time";
    var finishTimeInput = document.createElement("input");
    finishTimeInput.type = "text";
    finishTimeInput.id = "finish_time" + this.id;
    finishTimeInput.value = data.finish_time;
    finishTimeInput.onchange = () => {
      this.changed_data.finish_time = finishTimeInput.value;
    };
    finishTimeDiv.appendChild(finishTimeLabel);
    finishTimeDiv.appendChild(finishTimeInput);
    this.element.appendChild(finishTimeDiv);

    var dnfDiv = document.createElement("div");
    var dnfLabel = document.createElement("label");
    dnfLabel.htmlFor = "dnf" + this.id;
    dnfLabel.innerHTML = "Did Not Finish";
    var dnfInput = document.createElement("input");
    dnfInput.type = "checkbox";
    dnfInput.id = "dnf" + this.id;
    dnfInput.checked = data.DNF;
    dnfInput.onchange = () => {
      this.changed_data.DNF = dnfInput.checked;
    };
    dnfDiv.appendChild(dnfLabel);
    dnfDiv.appendChild(dnfInput);
    this.element.appendChild(dnfDiv);

    var dnsDiv = document.createElement("div");
    var dnsLabel = document.createElement("label");
    dnsLabel.htmlFor = "dns" + this.id;
    dnsLabel.innerHTML = "Did Not Start";
    var dnsInput = document.createElement("input");
    dnsInput.type = "checkbox";
    dnsInput.id = "dns" + this.id;
    dnsInput.checked = data.DNS;
    dnsInput.onchange = () => {
      this.changed_data.DNS = dnsInput.checked;
    };
    dnsDiv.appendChild(dnsLabel);
    dnsDiv.appendChild(dnsInput);
    this.element.appendChild(dnsDiv);

    var dqDiv = document.createElement("div");
    var dqLabel = document.createElement("label");
    dqLabel.htmlFor = "dq" + this.id;
    dqLabel.innerHTML = "Disqualified";
    var dqInput = document.createElement("input");
    dqInput.type = "checkbox";
    dqInput.id = "dq" + this.id;
    dqInput.checked = data.DQ;
    dqInput.onchange = () => {
      this.changed_data.DQ = dqInput.checked;
    };
    dqDiv.appendChild(dqLabel);
    dqDiv.appendChild(dqInput);
    this.element.appendChild(dqDiv);

    var athletes = document.getElementById("athletes");
    athletes.appendChild(this.element);
  }
}
