import {generateFastestPaths, generateGraph, pathForDest} from './pure_js.js';

let graph;
function calculate() {
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
            setTimeout(() => resolve(fn()), 10)
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

console.log("adding listener???");
document.getElementById("calc_button").addEventListener('click', () => calculate());