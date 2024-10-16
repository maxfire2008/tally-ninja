'use strict';
import { athleteSelectModal } from './athleteSelectModal.js';

export class AthleteInputCell {
    constructor(value, config) {
        this.init(value, config);
    }

    init(value, config) {
        this.value = value;
        this.config = config;
    }

    html(index) {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('td');
        this.element.classList.add('athlete_input_cell');

        this.button = document.createElement('button');
        this.button.dataset.index = index;
        this.button.textContent = this.value;
        this.updateButtonTextAndColour();
        this.button.addEventListener('click', () => {
            // athleteSelectModal((athlete) => {
            //     if (athlete !== null) {
            //         this.button.textContent = athlete.name;
            //         this.value = athlete.id;
            //     }
            // });
            this.value = prompt("Enter athlete ID", this.value);
            this.updateButtonTextAndColour();
        });

        this.element.appendChild(this.button);

        return this.element;
    }

    updateButtonTextAndColour() {
        fetch("/api/athlete/" + this.value).then((response) => {
            if (response.ok) {
                response.json().then((athlete) => {
                    this.button.textContent = athlete.name;
                    this.button.style.backgroundColor = this.config.teams[athlete.team].colour;
                    // if the colour is darker than 50% grey, use white text
                    let rgb = this.button.style.backgroundColor.split("rgb")[1].slice(1, -1).split(", ");
                    let brightness = Math.round(((parseInt(rgb[0]) * 299) + (parseInt(rgb[1]) * 587) + (parseInt(rgb[2]) * 114)) / 1000);
                    if (brightness < 128) {
                        this.button.style.color = "white";
                    }
                });
            }
        });
    }

    destroyHtml() {
        if (this.button !== undefined) {
            this.button.remove();
            delete this.button;
        }
    }

    focus() {
        this.button.focus();
    }

    value() {
        return this.value;
    }
}