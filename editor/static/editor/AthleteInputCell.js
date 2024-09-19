'use strict';
import { athleteSelectModal } from './AthleteSelectModal.js';

export class AthleteInputCell {
    constructor(value, config) {
        this.init(value, config);
    }

    init(value, config) {
        this.value = value;
        this.config = config;
    }

    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('button');
        this.element.textContent = this.value;
        fetch("/api/athlete/" + this.value).then((response) => {
            if (response.ok) {
                response.json().then((athlete) => {
                    this.element.textContent = athlete.name;
                    this.element.style.backgroundColor = this.config.teams[athlete.team].colour;
                    // if the colour is darker than 50% grey, use white text
                    let rgb = this.element.style.backgroundColor.split("rgb")[1].slice(1, -1).split(", ");
                    let brightness = Math.round(((parseInt(rgb[0]) * 299) + (parseInt(rgb[1]) * 587) + (parseInt(rgb[2]) * 114)) / 1000);
                    console.log(brightness);
                    if (brightness < 128) {
                        this.element.style.color = "white";
                    }
                });
            }
        });
        this.element.addEventListener('click', () => {
            athleteSelectModal((athlete) => {
                if (athlete !== null) {
                    this.element.textContent = athlete.name;
                    this.value = athlete.id;
                }
            });
        });

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