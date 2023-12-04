/* example usage:
/  data = {'type': 'race', 'name': 'Duathlon Short Course', 'distance': 'short_course', 'date': datetime.date(2023, 7, 1), 'results': {'donald_trump': {'finish_time': 3473430}, 'joe_biden': {'finish_time': 3382120}, 'kamala_harris': {'finish_time': 2537320}, 'hillary_clinton': {'finish_time': 2964450}, 'mitch_mcconnell': {'DNF': True}, 'nancy_pelosi': {'finish_time': 2172180}, 'bernie_sanders': {'finish_time': 9123850}, 'elizabeth_warren': {'finish_time': 2172180}}, '_filepath': '..\\sample_data\\results\\duathlon\\2023-07-duathlon-short.yaml', '_filename': '2023-07-duathlon-short.yaml'}
/  result_editor = new ResultEditor(data); */

class ResultEditor {
  constructor(data) {
    this.data = data;
    var header = document.getElementById("header");

    var nameDiv = document.createElement("div");
    var nameLabel = document.createElement("label");
    nameLabel.for = "name";
    nameLabel.innerHTML = "Name";
    var nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.id = "name";
    nameInput.value = data.name;
    nameInput.onchange = () => {
      this.data.name = nameInput.value;
    };
    nameDiv.appendChild(nameLabel);
    nameDiv.appendChild(nameInput);
    header.appendChild(nameDiv);

    var distanceDiv = document.createElement("div");
    var distanceLabel = document.createElement("label");
    distanceLabel.for = "distance";
    distanceLabel.innerHTML = "Distance";
    var distanceInput = document.createElement("input");
    distanceInput.type = "text";
    distanceInput.id = "distance";
    distanceInput.value = data.distance;
    distanceInput.onchange = () => {
      this.data.distance = distanceInput.value;
    };
    distanceDiv.appendChild(distanceLabel);
    distanceDiv.appendChild(distanceInput);
    header.appendChild(distanceDiv);

    var dateDiv = document.createElement("div");
    var dateLabel = document.createElement("label");
    dateLabel.for = "date";
    dateLabel.innerHTML = "Date";
    var dateInput = document.createElement("input");
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
    for (var athlete_id in data.results) {
      this.results.push(new Result(athlete_id, data.results[athlete_id]));
    }
  }
}

class Result {
  constructor(athlete_id, data) {
    this.athlete_id = athlete_id;
    this.data = data;

    this.element = document.createElement("div");
    this.element.className = "result";

    var athleteDiv = document.createElement("div");
    var athleteLabel = document.createElement("label");
    athleteLabel.for = "athlete";
    athleteLabel.innerHTML = "Athlete";
    var athleteInput = document.createElement("input");
    athleteInput.type = "text";
    athleteInput.id = "athlete";
    athleteInput.value = athlete_id;
    athleteInput.onchange = () => {
      this.athlete_id = athleteInput.value;
    };
    athleteDiv.appendChild(athleteLabel);
    athleteDiv.appendChild(athleteInput);
    this.element.appendChild(athleteDiv);

    var finishTimeDiv = document.createElement("div");
    var finishTimeLabel = document.createElement("label");
    finishTimeLabel.for = "finish_time";
    finishTimeLabel.innerHTML = "Finish Time";
    var finishTimeInput = document.createElement("input");
    finishTimeInput.type = "text";
    finishTimeInput.id = "finish_time";
    finishTimeInput.value = data.finish_time;
    finishTimeInput.onchange = () => {
      this.data.finish_time = finishTimeInput.value;
    };
    finishTimeDiv.appendChild(finishTimeLabel);
    finishTimeDiv.appendChild(finishTimeInput);
    this.element.appendChild(finishTimeDiv);

    var dnfDiv = document.createElement("div");
    var dnfLabel = document.createElement("label");
    dnfLabel.for = "dnf";
    dnfLabel.innerHTML = "Did Not Finish";
    var dnfInput = document.createElement("input");
    dnfInput.type = "checkbox";
    dnfInput.id = "dnf";
    dnfInput.checked = data.DNF;
    dnfInput.onchange = () => {
      this.data.DNF = dnfInput.checked;
    };
    dnfDiv.appendChild(dnfLabel);
    dnfDiv.appendChild(dnfInput);
    this.element.appendChild(dnfDiv);

    var dnsDiv = document.createElement("div");
    var dnsLabel = document.createElement("label");
    dnsLabel.for = "dns";
    dnsLabel.innerHTML = "Did Not Start";
    var dnsInput = document.createElement("input");
    dnsInput.type = "checkbox";
    dnsInput.id = "dns";
    dnsInput.checked = data.DNS;
    dnsInput.onchange = () => {
      this.data.DNS = dnsInput.checked;
    };
    dnsDiv.appendChild(dnsLabel);
    dnsDiv.appendChild(dnsInput);
    this.element.appendChild(dnsDiv);

    var dqDiv = document.createElement("div");
    var dqLabel = document.createElement("label");
    dqLabel.for = "dq";
    dqLabel.innerHTML = "Disqualified";
    var dqInput = document.createElement("input");
    dqInput.type = "checkbox";
    dqInput.id = "dq";
    dqInput.checked = data.DQ;
    dqInput.onchange = () => {
      this.data.DQ = dqInput.checked;
    };
    dqDiv.appendChild(dqLabel);
    dqDiv.appendChild(dqInput);
    this.element.appendChild(dqDiv);

    var athletes = document.getElementById("athletes");
    athletes.appendChild(this.element);
  }
}
