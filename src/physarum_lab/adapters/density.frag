uniform sampler2D field;
uniform vec2 size;
uniform vec2 center;
uniform float zoom;
uniform float resolution;
uniform float bloom;
uniform float show_guide;
uniform float chase;
uniform vec3 color0;
uniform vec3 color1;
uniform vec3 color2;
uniform vec3 color3;
uniform vec3 color4;

float luminance(vec2 uv) {
    return texture2D(field, uv).r;
}

vec3 palette(float value) {
    float q = clamp(value, 0., 1.) * 4.;
    if (q < 1.) return mix(color0, color1, q);
    if (q < 2.) return mix(color1, color2, q - 1.);
    if (q < 3.) return mix(color2, color3, q - 2.);
    return mix(color3, color4, q - 3.);
}

void main() {
    float side = min(size.x, size.y);
    vec2 local = (gl_FragCoord.xy - size * .5) / side;
    if (max(abs(local.x), abs(local.y)) > .5) {
        gl_FragColor = vec4(color0, 1.);
        return;
    }
    vec2 uv = local / zoom + center;
    vec3 rgb;
    if (chase > .5) {
        vec2 layers = texture2D(field, uv).rg;
        rgb = (vec3(3, 8, 14) + layers.r * vec3(232, 222, 196)
               + layers.g * vec3(242, 124, 41)) / 255.;
    } else {
        rgb = palette(luminance(uv));
        vec2 d = vec2(3. / resolution, 0.);
        vec3 light = max(palette(luminance(uv + d)) - vec3(.392), 0.);
        light += max(palette(luminance(uv - d)) - vec3(.392), 0.);
        light += max(palette(luminance(uv + d.yx)) - vec3(.392), 0.);
        light += max(palette(luminance(uv - d.yx)) - vec3(.392), 0.);
        rgb += light * bloom * .25;
    }
    if (show_guide > .5) {
        float alpha = texture2D(field, uv).b;
        rgb = mix(rgb, vec3(.74, .42, .22), .30 * alpha);
    }
    gl_FragColor = vec4(clamp(rgb, 0., 1.), 1.);
}
