import {
    generateFastestPaths, generateGraph, pathForDest, SETTINGS
} from './angle_finder.js';

let graph;

function calculate() {
    SETTINGS.ESS_COUNT = Number((document.getElementById("ess_count") as HTMLInputElement).value);
    SETTINGS.SWORD_ENABLED = (document.getElementById("sword_enabled") as HTMLInputElement).checked;
    SETTINGS.BIGGORON_ENABLED = (document.getElementById("biggoron_enabled") as HTMLInputElement).checked;
    SETTINGS.NO_CARRY_ENABLED = (document.getElementById("no_carry_enabled") as HTMLInputElement).checked;
    SETTINGS.SHIELD_CORNER_ENABLED = (document.getElementById("shield_enabled") as HTMLInputElement).checked;

    const src_value = (document.getElementById("src_angles") as HTMLTextAreaElement).value;
    const src_angles = src_value.split('\n').map(v => Number.parseInt(v.trim(), 16) & 0xFFFF);
    const dest_value = (document.getElementById("dest_angle") as HTMLInputElement).value;
    const dest_angle = Number.parseInt(dest_value, 16) & 0xFFFF;

    const outPath = document.getElementById("out_path");
    outPath.innerHTML = '';

    const loadEle = document.createElement('li')
    loadEle.innerText = 'calculating...';
    outPath.appendChild(loadEle);

    async function delay<T>(fn: () => T): Promise<T> {
        return new Promise<T>(function (resolve) {
            requestAnimationFrame(() => {
                requestAnimationFrame(()=> resolve(fn()));
            });
        });
    }

    async function run() {
        if (!graph) {
            loadEle.innerText = `Generating graph...`;
            graph = await delay(() => generateGraph());
        }
        const fastests = []
        let path: string[] = null;
        for (let src_angle of src_angles) {
            loadEle.innerText = `Calculating fastest paths for ${src_angle}`;
            const fast = await delay(() => generateFastestPaths(graph, src_angle).backPath);
            const nextPath = pathForDest(fast, dest_angle);
            console.log(nextPath.length, nextPath);
            if (path == null || path.length > nextPath.length) {
                path = nextPath;
            }
        }

        console.log("Path: ", path);
        outPath.innerHTML = '';
        for (const line of path) {
            if (line === '') continue;
            const ele = document.createElement('li')
            ele.innerText = line;
            outPath.appendChild(ele);
        }
    }

    setTimeout(() => {
        run().then(() => console.log("Done!"));
    })
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("Adding listeners")
    function clearGraph() {
        console.log("Clearing graph");
        graph = null;
    }
    document.getElementById("calc_button").addEventListener('click', () => calculate());
    document.getElementById("ess_count").addEventListener('change', clearGraph);
    document.getElementById("sword_enabled").addEventListener('change', clearGraph);
    document.getElementById("biggoron_enabled").addEventListener('change', clearGraph);
    document.getElementById("no_carry_enabled").addEventListener('change', clearGraph);
    document.getElementById("shield_enabled").addEventListener('change', clearGraph);
});