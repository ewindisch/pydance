#!/usr/bin/ruby -w
# A script for reducing the size of PyDDR step files
# It's a POS design-wise, but it seems to work.
# Public domain.

lines = []
lines2 = []

if ! ARGV[0] or ! File.readable? ARGV[0]
  puts "stepshrink v2, by Joe Wreschnig <piman@sacredchao.net>"
  puts "Shrink PyDDR step files by consolidating empty steps."
  puts "Usage:\n  #{$0} filename > newfilename"
  exit
end

File.open(ARGV[0]).each_line do |line|
  lines.push line.squeeze(" ").strip
end

i = 0

steps = /^steps (\d\d\s+\d\d\s+\d\d\s+\d\d)/;
eight = /^eight (\d\d\s+\d\d\s+\d\d\s+\d\d)/;
qurtr = /^qurtr (\d\d\s+\d\d\s+\d\d\s+\d\d)/;
e_steps = /^steps 00\s+00\s+00\s+00/;
e_eight = /^eight 00\s+00\s+00\s+00/;

# First pass, compress delays
lines.each do |line|
  if ! e_eight.match(line)
    if i % 2 == 1 then lines2.push "eight 00 00 00 00" end
    if i > 1
      lines2.push "delay #{i/2}"
    end
    lines2.push line.strip
    i = 0
  else
    i += 1
  end
end

lines = lines2
lines2 = []

# Second pass, compress 16th notes and 8th notes
lines.each do |line|
  if e_steps.match(line) and steps.match(lines2[-1])
    lines2.pop
    lines2.push "eight #{$1}"
  elsif e_eight.match(line) and eight.match(lines2[-1])
    lines2.pop
    lines2.push "qurtr #{$1}"
  else
    lines2.push line.strip
  end
end

lines = lines2
lines2 = []

# Third pass, compress delays + 4ths into half/whole notes
lines.each do |line|
  if line =~ /^delay/ and qurtr.match(lines2[-1])
    val = $1.dup
    if line =~ /^delay (\d+)/
      lines2.pop
      if $1.to_i > 3
	lines2.push "whole #{val}"
	lines2.push "delay #{$1.to_i - 3}"
      elsif $1.to_i == 3
	lines2.push "whole #{val}"
      elsif $1.to_i == 2
	lines2.push "halfn #{val}"
	lines2.push "delay 1"
      elsif $1.to_i == 1
	lines2.push "halfn #{val}"
      else
	lines2.push line
      end
    end
  else
    lines2.push line
  end
end

lines = lines2

puts lines
