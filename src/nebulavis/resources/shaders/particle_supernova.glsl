
#version 330
layout(std140) uniform BandData { float bands[256]; };
layout(std140) uniform FrameData { float frame[16]; };
uniform float uTime;
out vec4 fragColor;

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0) - 0.5;
float dist = length(uv);
float pulse = bands[int(mod(uTime * 10.0, 32.0))];
float burst = exp(-dist * 8.0) * (0.5 + pulse * 2.0);
vec3 color = vec3(1.2 * burst, 0.4 + pulse, 0.6 + burst * 0.5);
fragColor = vec4(color, 1.0);
}
