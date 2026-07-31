#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt

import json

from ShockwaveParser import ShockwaveParser, CastType

def main(argv):
	
	#print("")

	#meta = open( "metadata.json", "w")
	#meta.write( json.dumps( test.castLibraries, indent=4 ) )
	#meta.close()

	inputfile = ""
	extract = False
	extractRaw = False
	library = "Internal"
	member = -1
	showFiles = False
	showCasts = False
	packImages = False
	forceLittle = False
	useName = False

	try:
		opts, args = getopt.getopt(argv,"hi:erl:m:pn",["input=","extract","raw","library","member","fileinfo","castinfo","pack", "little", "name"])
	except getopt.GetoptError:
		print('test.py -i <inputfile> -e -l <library> -m <member> --fileinfo --castinfo')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('test.py -i <inputfile> -e -l <library> -m <member> --fileinfo --castinfo')
			sys.exit()
		elif opt in ("-i", "--input"):
			inputfile = arg
		elif opt in ("-e", "--extract"):
			extract = True
		elif opt in ("-r", "--raw"):
			extractRaw = True
		elif opt in ("-l", "--library"):
			library = arg
		elif opt in ("-m", "--member"):
			member = int(arg)
		elif opt in ("-fi", "--fileinfo"):
			showFiles = True
		elif opt in ("-ci", "--castinfo"):
			showCasts = True
		elif opt in ("-p", "--pack"):
			packImages = True
		elif opt in ("-n", "--name"):
			useName = True
		elif opt in ("--little"):
			forceLittle = True

	
	if inputfile != "":
		
		rd = ShockwaveParser( inputfile )

		if forceLittle:
			rd.forceLittle = True

		rd.read()

		if showFiles:
			for f in rd.fileEntries:
				print(f)

		if showCasts:

			if member > -1:

				e = rd.getCastMember(library, member)

				if not e:
					raise Exception("Cast member not found")
					return

				print("")
				print("[" + str(member) + "]")
				print(" Source: " + str( rd.baseName ) )
				print(" Type: " + str( CastType( e["castType"] ) ) )
				print(" Name: " + str( e["name"] ) )
				print(" Cast offset: " + str( e["dataOffset"] ) )
				print(" Cast length: " + str( e["dataLength"] ) )

				if e["castType"] == CastType.SOUND.value:
					print(" Looped: " + str( e["soundLooped"] ) )

				print("")
				print(" Linked files (" + str( len( e["linkedEntries"] ) ) + "):" )
				for l in e["linkedEntries"]:
					lf = rd.fileEntries[l]
					print("  [" + str(l) + "] " + lf["type"] + " (len " + str(lf["dataLength"]) + ", off " + str(lf["dataOffset"]) + ")")

				print("")
				print("Metadata")
				print( e )

			else:
				
				print("")

				for l in rd.castLibraries:

					print("[Cast library]")
					print("Name: " + l["name"])
					print("Member count: " + str(l["memberCount"]))

					if not 'members' in l:
						print("(no member table)")
						print("")
						continue

					print("Members (" + str( len( l['members'] ) ) + "):")
					for c in l['members']:
						e = l['members'][c]
						print(" [" + str(c) + "]")
						print(" Type: " + str( CastType( e["castType"] ) ) )
						print(" Name: " + str( e["name"] ) )
						print(" Cast offset: " + str( e["dataOffset"] ) )
						print(" Cast length: " + str( e["dataLength"] ) )
						print(" Linked files: " + str( len( e["linkedEntries"] ) ) )
						for lk in e["linkedEntries"]:
							lf = rd.fileEntries[lk]
							print("  [" + str(lk) + "] " + lf["type"] + " (len " + str(lf["dataLength"]) + ", off " + str(lf["dataOffset"]) + ")")
						print("")

					print("")

		if extract:

			dirName = os.path.basename( rd.fileName ).upper()

			basePath = "cst_out_new/" + dirName

			if not os.path.exists(basePath):
				os.makedirs(basePath)

			if member > -1:

				m = rd.getCastMember("Internal" if library == "" else library, member)

				if not m:
					raise Exception("Cast member not found")
					return
				
				path = basePath + "/" + m['castLibrary']

				rd.extractCastMember(m['castLibrary'], member, extractRaw, path, useName)

			else:

				pack_files = {}

				imageData = []

				# loop through cast libraries
				
				print("Extract files")

				pack_files[ dirName ] = []

				highestSampleRate = 0

				for l in rd.castLibraries:

					if not 'members' in l:
						continue

					fileOutPath = basePath + "/" + l['name']

					assetPath = "assets/" + dirName + "/" + l['name']

					for c in l['members']:

						if not os.path.exists(fileOutPath):
							os.makedirs(fileOutPath)

						rd.extractCastMember(l['name'], c, extractRaw, fileOutPath, useName)

						if l['members'][c]['castType'] == CastType.BITMAP.value and l['members'][c]['imageWidth'] > 0:
							# imageData.append([l['name'], c, fileOutPath + "/" + str(c) + ".bmp"])
							imageData.append([l['name'], c, fileOutPath + "/" + str(c) + ".png"])

						# sample rate
						if l['members'][c]['castType'] == CastType.SOUND.value and l['members'][c]['soundSampleRate'] > 0:
							if l['members'][c]['soundSampleRate'] > highestSampleRate:
								highestSampleRate = l['members'][c]['soundSampleRate']

				# json output
				
				print("Output metadata JSON")
				
				meta = {}

				meta["libraries"] = []

				meta["dir"] = rd.baseName

				# if atlas_list != None:
				# 	meta["spriteSheets"] = len( atlas_list )

				for l in rd.castLibraries:

					lib = {}
					lib["name"] = l["name"]
					lib["members"] = {}

					if 'members' in l:
						for c in l['members']:

							if l['members'][c]['castType'] == CastType.SCRIPT.value:
								continue
							
							m = l['members'][c].copy()

							m.pop('castDataLength', None)
							m.pop('castEndDataLength', None)
							m.pop('castFieldOffsets', None)
							m.pop('castFieldData', None)
							m.pop('castFieldDataLength', None)
							m.pop('castUnknown', None)
							m.pop('castSlot', None)
							m.pop('castLibrary', None)
							m.pop('fileSlot', None)
							m.pop('dataOffset', None)
							m.pop('dataLength', None)
							m.pop('linkedEntries', None)

							lib["members"][c] = m


					meta["libraries"].append(lib)

				fEntryOut = open( basePath + "/metadata.json", "w")
				fEntryOut.write( json.dumps( meta ) )
				fEntryOut.close()

				pack_files[ dirName ].append({
					"type": "json",
					"key": dirName + "_metadata",
					"url": "assets/" + dirName + "/metadata.json"
				})


				print("Output pack JSON")

				fFilesOut = open( basePath + "/pack.json", "w")
				fFilesOut.write( json.dumps( pack_files ) )
				fFilesOut.close()

if __name__ == "__main__":
	main(sys.argv[1:])