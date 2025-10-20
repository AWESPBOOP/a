
#version 330
layout(std140) uniform BandData { float bands[256]; };
uniform float uTime;
out vec4 fragColor;

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0);
int index = int(floor(uv.x * 96.0));
float value = bands[index];
float height = smoothstep(1.0 - value, 1.0, uv.y);
vec3 color = mix(vec3(0.1), vec3(value, 0.6, 0.9), height);
fragColor = vec4(color, 1.0);
}
