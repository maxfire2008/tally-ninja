'use strict';

export class DurationInputCell {
    constructor(value, config) {
        this.init(value, config);
    }

    init(value, config) {
        this.value = value;
        this.config = config;
    }

    millisecondsToHhmmss(milliseconds) {
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

    hhmmssToMilliseconds(hhmmss) {
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


    html(index) {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('td');

        this.input = document.createElement('input');
        this.input.dataset.index = index;
        this.input.type = 'text';
        this.input.value = this.millisecondsToHhmmss(this.value);

        this.input.addEventListener('input', () => {
            this.value = this.hhmmssToMilliseconds(this.element.value);
        });

        this.element.appendChild(this.input);

        return this.element;
    }

    destroyHtml() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }
    }

    focus() {
        this.input.focus();
    }

    value() {
        return this.value;
    }
}