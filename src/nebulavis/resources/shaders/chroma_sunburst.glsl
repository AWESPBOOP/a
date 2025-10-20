
#version 330
layout(std140) uniform BandData { float bands[256]; };
uniform float uTime;
out vec4 fragColor;

vec3 palette(float t) {
return vec3(0.5 + 0.5 * cos(6.2831 * (t + vec3(0.0, 0.33, 0.67))));
}

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0) - 0.5;
float angle = atan(uv.y, uv.x) / 6.2831;
float radius = length(uv);
float energy = bands[int(mod(angle * 256.0, 128.0))];
vec3 color = palette(angle + uTime * 0.1) * (0.3 + energy * 2.0) * exp(-radius * 2.0);
fragColor = vec4(color, 1.0);
}
