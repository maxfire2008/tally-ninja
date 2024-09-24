'use strict';

export class DurationInputCell {
    constructor(value, config) {
        this.init(value, config);
    }

    init(value, config) {
        this.value = value;
        this.config = config;
    }

    microsecondsToHhmmss(microseconds) {
        if (microseconds === undefined) {
            return "";
        }
        if (!Number.isInteger(microseconds)) {
            throw new TypeError("microseconds must be an integer");
        }

        const hours = Math.floor(microseconds / 3600000000);
        const minutes = Math.floor((microseconds % 3600000000) / 60000000);
        const seconds = Math.floor((microseconds % 60000000) / 1000000);
        const mcrs = (microseconds % 1000000);

        console.log(hours, minutes, seconds, mcrs);

        let output = "";

        if (hours > 0) {
            output += hours + ":";
        }
        if (minutes > 0) {
            output += minutes.toString().padStart(2, "0") + ":";
        }
        output += seconds.toString().padStart(2, "0");
        if (mcrs > 0) {
            const mcrss = mcrs.toString().padStart(6, "0")
            // trim trailing zeros (DO NOT USE REGEX)
            let i = 5;
            while (mcrss[i] === "0") {
                i--;
            }
            output += "." + mcrss.substring(0, i + 1);
        }

        return output;
    }

    hhmmssTomicroseconds(hhmmss) {
        if (hhmmss === "" || hhmmss === undefined) {
            return undefined;
        }

        if (hhmmss.split(".").length >= 2 && hhmmss.split(".")[1].length > 6) {
            throw new Error("More than 6 digits after the decimal point");
        }

        const hhmmssSplit = hhmmss.split(":");
        const secondsSplit = hhmmssSplit[hhmmssSplit.length - 1].split(".");
        let microseconds = parseInt(secondsSplit[0]) * 1000000;

        if (secondsSplit.length > 1) {
            microseconds += parseInt(secondsSplit[1].padEnd(6, "0"));
        }

        if (hhmmssSplit.length > 1) {
            microseconds += parseInt(hhmmssSplit[hhmmssSplit.length - 2]) * 60000000;
        }
        if (hhmmssSplit.length > 2) {
            microseconds += parseInt(hhmmssSplit[hhmmssSplit.length - 3]) * 3600000000;
        }

        return microseconds;
    }


    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('td');

        this.input = document.createElement('input');
        this.input.type = 'text';
        this.input.value = this.microsecondsToHhmmss(this.value);

        this.sixDPAttempts = 0;

        this.input.addEventListener('input', () => {
            try {
                this.value = this.hhmmssTomicroseconds(this.input.value);
            } catch (e) {
                if (e.toString() === "Error: More than 6 digits after the decimal point") {
                    this.input.value = this.input.value.substring(0, this.input.value.length - 1);
                    this.sixDPAttempts++;
                    if (this.sixDPAttempts > 3) {
                        alert("You can only have 6 decimal places");
                        this.sixDPAttempts = 0;
                    }
                }
            }
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

    value() {
        return this.value;
    }
}